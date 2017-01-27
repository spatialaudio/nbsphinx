#!/bin/sh

set -e

fmt='
git checkout %(refname)
git rebase master
git push origin HEAD:%(refname:strip=3) --force
'

eval "$(git for-each-ref --shell --format="$fmt" refs/remotes/origin/*-theme)"

git checkout master
