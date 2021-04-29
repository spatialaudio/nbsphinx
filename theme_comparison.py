#!/usr/bin/env python3
"""Build multiple versions of the docs with different themes.

If no THEME-NAMES are given, all theme branches will be built.

All options after -- are passed to Sphinx.

A requirements file can be created with the --requirements (or -r) flag.
Those requirements can be installed with:

    python3 -m pip install -r theme_comparison/theme_requirements.txt

"""
import argparse
from pathlib import Path

from sphinx.cmd.build import build_main


parser = argparse.ArgumentParser(
    description=__doc__,
    usage='%(prog)s [OPTIONS] [THEME-NAMES] [-- SPHINX-OPTIONS]',
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument(
    '-l', '--list-themes', action='store_true',
    help='show list of available themes and exit')
parser.add_argument(
    '-r', '--requirements', action='store_true',
    help='create theme_requirements.txt and exit')
parser.add_argument(
    '-f', '--fetch', action='store_true',
    help='fetch latest data from "upstream"')
parser.add_argument(
    'themes', metavar='THEME-NAMES', nargs=argparse.REMAINDER,
    help='theme names (according to "*-theme" branch names)')
args = parser.parse_args()

try:
    import git
except ImportError as e:
    parser.exit(
        'The Python package GitPython has to be installed:\n\n'
        '    python3 -m pip install GitPython\n')

main_dir = Path(__file__).resolve().parent / 'theme_comparison'
main_dir.mkdir(exist_ok=True)
repo = git.Repo(main_dir, search_parent_directories=True)
for remote in repo.remotes:
    if any('spatialaudio/nbsphinx' in url for url in remote.urls):
        if args.fetch:
            remote.fetch()
        break
else:
    if args.fetch:
        remote = repo.create_remote(
            'upstream',
            'https://github.com/spatialaudio/nbsphinx.git')
        remote.fetch()
    else:
        parser.error('no upstream remote found, use --fetch to download')

available_themes = (
    (ref.remote_head[:-len('-theme')], ref.name)
    for ref in remote.refs
    if ref.remote_head.endswith('-theme')
)

if args.list_themes:
    for theme, _ in available_themes:
        print(theme)
    parser.exit(0)

try:
    end_of_args = args.themes.index('--')
except ValueError:
    end_of_args = len(args.themes)
requested_themes = args.themes[:end_of_args]
sphinx_options = args.themes[end_of_args + 1:]

if requested_themes:
    selected_themes = []
    for theme, branch in available_themes:
        if theme in requested_themes:
            selected_themes.append((theme, branch))
            requested_themes.remove(theme)
    if requested_themes:
        parser.error(f'theme(s) not found: {requested_themes}')
else:
    selected_themes = available_themes

worktree_dir = main_dir / '_worktree'
if not worktree_dir.exists():
    repo.git.worktree('prune')
    repo.git.worktree('add', worktree_dir, '--detach')

worktree = git.Git(worktree_dir)
head_commit = repo.git.rev_parse('HEAD')
worktree.reset(head_commit, '--hard')
stash_commit = repo.git.stash('create', '--include-untracked')
if stash_commit:
    worktree.merge(stash_commit)
base_commit = worktree.rev_parse('HEAD')


def run_with_all_themes(func):
    try:
        for name, branch in selected_themes:
            worktree.cherry_pick(branch)
            func(name, branch)
            worktree.reset(base_commit, '--hard')
    finally:
        worktree.reset(head_commit, '--hard')
        repo.git.worktree('prune')


if args.requirements:
    requirements = set()

    def collect_requirements(name, branch):
        path = worktree_dir / 'doc' / 'requirements.txt'
        requirements.update(path.read_text().splitlines())

    run_with_all_themes(collect_requirements)
    path = Path(repo.working_tree_dir) / 'doc' / 'requirements.txt'
    requirements.difference_update(path.read_text().splitlines())
    path = main_dir / 'theme_requirements.txt'
    path.write_text('\n'.join(sorted(requirements)))
    print('Requirements written to', path)
    parser.exit(0)


def build_docs(name, branch):
    print('#' * 80)
    print('#', name.upper().center(76), '#')
    print('#' * 80)
    result = build_main([
        str(worktree_dir / 'doc'),
        str(main_dir / name),
        '-d', str(main_dir / '_cache'),
        '-Drelease=dummy',
        '-Dversion=dummy',
        '-Dtoday=dummy',
        '-Dhtml_title=nbsphinx-theme-comparison',
        *sphinx_options,
    ])
    if result != 0:
        parser.exit(result)
    print('')


run_with_all_themes(build_docs)
