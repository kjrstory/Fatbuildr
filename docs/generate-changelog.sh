#!/bin/sh

mkdir -p generated-doc/modules/misc/partials
# Replace issue with hyperlinks to github issues
sed -i 's/\(#\([0-9]\+\)\)/[#\2](https:\/\/github.com\/rackslab\/fatbuildr\/issues\/\2\)/g' CHANGELOG.md
pandoc --from markdown --to asciidoctor CHANGELOG.md --output generated-doc/modules/misc/partials/CHANGELOG.adoc
