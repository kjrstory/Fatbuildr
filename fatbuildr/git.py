#!/usr/bin/env python3
#
# Copyright (C) 2021 Rackslab
#
# This file is part of Fatbuildr.
#
# Fatbuildr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatbuildr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fatbuildr.  If not, see <https://www.gnu.org/licenses/>.

import subprocess
import re
from datetime import datetime

import pygit2
from debian import deb822

from .log import logr

logger = logr(__name__)


def parse_patch(patch):
    """Read the given patch file and parse metadata in deb822 format."""
    # read the patch and parse metadata
    with open(patch, 'rb') as fh:
        content = fh.read()
    return deb822.Deb822(content)


def is_meta_generic(meta):
    """Returns True if the patch metadata indicates a generic (ie. not version
    specific) patch, or False otherwise."""
    return 'Generic' in meta and meta['Generic'] == 'yes'


class GitRepository:
    def __init__(self, path, author, email):
        self.path = path
        self._repo = pygit2.init_repository(path, bare=False)
        self._initial_commit(author, email)

    def _initial_commit(self, author, email):
        ref = "HEAD"
        parents = []
        message = "Initial commit"
        self._base_commit(ref, parents, author, email, message)

    def _commit(self, author, email, title, meta, files):
        ref = self._repo.head.name
        parents = [self._repo.head.target]
        message = title + "\n\n" + str(meta)
        self._base_commit(ref, parents, author, email, message, files)

    def _base_commit(self, ref, parents, author, email, message, files=None):
        """Method actually performing the commit on ref, over the given parents
        with the given author, email and message. The files argument must either
        be None, or a list of files to index and commit. The paths must be
        relative to the root of the Git repository. If files is None (default),
        all modified files are selected for the commit."""
        index = self._repo.index
        if files is None:
            index.add_all()
        else:
            # add given files list to index
            for _file in files:
                index.add(_file)
        index.write()
        author_s = pygit2.Signature(author, email)
        committer_s = pygit2.Signature(author, email)
        tree = index.write_tree()
        self._repo.create_commit(
            ref, author_s, committer_s, message, tree, parents
        )

    def walker(self):
        """Returns an iterator over the commits in Git history."""
        return self._repo.walk(
            self._repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL
        )

    def diff(self, commit):
        """Returns the diff as a string between a commit and its first
        parent. When the diff is empty, None is returned."""
        return self._repo.diff(commit.parents[0], commit).patch

    def import_patches(self, patches_dir, version):
        """Import patches in patches_dir, starting with generic followed by
        version specific patches."""

        patches_subdirs = [
            patches_dir.joinpath('generic'),
            patches_dir.joinpath(version),
        ]

        for patches_subdir in patches_subdirs:
            self._import_patches_subdir(patches_subdir)

    def _import_patches_subdir(self, patches_subdir):
        """Import patches in patches_subdir sorted by name into successive
        commits."""

        # If the patches directory does not exist, nothing to do here
        if not patches_subdir.exists():
            return

        sorted_patches = sorted([patch for patch in patches_subdir.iterdir()])

        for patch in sorted_patches:
            self._apply_patch(patch)

    def _apply_patch(self, patch):

        with open(patch, 'rb') as fh:
            content = fh.read()

        # Extract commit title (1st line) from patch filename, by removing
        # the patch index before the first dash.
        title = patch.name.split('-', 1)[1]

        # Parse metadata of the patch in deb822 format
        meta = deb822.Deb822(content)
        author_key = None
        # Search for accepted author key in metadata
        for key in ['Author', 'From']:
            if key in meta:
                author_key = key
        # If an accepted author key has been found in meta, parse it. Otherwise
        # use default 'unknown' author
        if author_key:
            author_re = re.match(
                r'(?P<author>.+) <(?P<email>.+)>', meta[author_key]
            )
            author = author_re.group('author')
            email = author_re.group('email')
            del meta[author_key]
        else:
            author = 'Unknown Author'
            email = 'unknown@email.com'

        # If the patch is loaded from the generic subdir, add the corresponding
        # field in commit metadata
        if patch.parent.name == 'generic':
            meta['Generic'] = 'yes'

        # Apply the patch. The patch command is used because pygit2 does not
        # offer API to apply patches that allows not well formatted patch, with
        # fuzzing or offset.
        #
        # The --force argument prevents patch from asking questions
        # interactively.
        #
        # The backup and reject files are discarded as they do not add value
        # compared to git repository.
        cmd = [
            "patch",
            "--force",
            "--no-backup-if-mismatch",
            "--reject-file=-",
            "-p1",
        ]
        logger.info("Applying patch %s", patch.name)
        subprocess.run(cmd, input=content, cwd=self.path)

        # Commit modifications
        self._commit(author, email, title, meta, files=None)

    def export_queue(self, patches_dir, version):
        """Export all commits in the repository into successive patches in
        patches_dir."""

        # Create destination patches directory if it does not exist yet
        if not patches_dir.exists():
            logger.debug("Creating artifact patches directory %s", patches_dir)
            patches_dir.mkdir()

        # Remove all existing patches
        for patches_subdir in [
            patches_dir.joinpath('generic'),
            patches_dir.joinpath(version),
        ]:
            if patches_subdir.exists():
                for patch in patches_subdir.iterdir():
                    logger.debug(
                        "Removing old patch %s/%s",
                        patch.parent.name,
                        patch.name,
                    )
                    patch.unlink()

        # Count generic and version specific commits
        index_generic = 0
        index_version = 0

        for commit in self.walker():
            if not commit.parents:
                break
            meta = deb822.Deb822(commit.message.split("\n", 2)[2])
            if is_meta_generic(meta):
                index_generic += 1
            else:
                index_version += 1

        logger.debug(
            "Found %d generic and %s version specific commits in patch queue",
            index_generic,
            index_version,
        )

        # Export patches
        for commit in self.walker():
            if not commit.parents:
                break
            meta = deb822.Deb822(commit.message.split("\n", 2)[2])
            if is_meta_generic(meta):
                self._export_commit(
                    patches_dir.joinpath('generic'), index_generic, commit, meta
                )
                index_generic -= 1
            else:
                self._export_commit(
                    patches_dir.joinpath(version), index_version, commit, meta
                )
                index_version -= 1

    def _export_commit(self, patches_subdir, index, commit, meta):

        meta['Author'] = f"{commit.author.name} <{commit.author.email}>"
        patch_name = commit.message.split('\n')[0]
        patch_path = patches_subdir.joinpath(f"{index:04}-{patch_name}")

        # If the Generic field is present in commit metadata, remove it. The
        # patch is saved in generic subdirectory, this is how Fatbuildr knowns
        # the exported patch is generic.
        if 'Generic' in meta:
            del meta['Generic']

        logger.info(
            f"Generating patch file {patches_subdir.name}/{patch_path.name}"
        )

        diff = self.diff(commit)
        # Check if the diff is empty. When it is empty, just warn user, else
        # save patch in file.
        if diff:
            # Create patches subdirectory if missing
            if not patches_subdir.exists():
                logger.debug("Creating patches subdirectory %s", patches_subdir)
                patches_subdir.mkdir()
                patches_subdir.chmod(0o755)
            with open(patch_path, 'w+') as fh:
                fh.write(str(meta) + '\n\n')
                fh.write(diff)
        else:
            logger.warning("Patch diff is empty, skipping patch generation")

    def commit_export(
        self,
        patches_dir,
        index,
        title,
        author,
        email,
        description,
        files,
    ):
        """Commit the modifications in the git repository and export these
        modifications into a patch file in patches_dir."""

        meta = deb822.Deb822()
        meta['Description'] = description
        meta['Forwarded'] = "no"
        meta['Last-Update'] = datetime.today().strftime('%Y-%m-%d')

        self._commit(author, email, title, meta, files)

        last_commit = self._repo[self._repo.head.target]

        # Create patches directory if if does not exist.
        if not patches_dir.exists():
            logger.debug(
                "Creating artifact version patches directory %s", patches_dir
            )
            patches_dir.mkdir(parents=True)

        meta = deb822.Deb822(last_commit.message.split("\n", 2)[2])
        self._export_commit(patches_dir, index, last_commit, meta)
