# MolModa Documentation

This repository contains the documentation for MolModa, developed by the Durrant Lab at the University of Pittsburgh.

## Environment

We use GNU Make to automate development; thus, please make sure you have this installed on your system.
This repository uses [Material for MKDocs](https://squidfunk.github.io/mkdocs-material/) that is managed with a conda environment.
Run

```bash
make environment
```

to create a conda environment called `molmoda-docs-dev`.
All `make` command automatically use this conda environment.

## Editing

You can create a live server to view changes in real time by running the following command.

```bash
make serve
```

## Building

To compile the website, run the following bash command in the repository root.

```bash
make docs
```

This will create a `public/` directory with the website's HTML files.
You can then run the following command to open documentation in your browser.

```bash
make open-docs
```

## Deploying

We use [bump-my-version](https://github.com/callowayproject/bump-my-version) to release a new version.
This will create a git tag that is used by [poetry-dynamic-version](https://github.com/mtkennerly/poetry-dynamic-versioning) to generate version strings.

However, we are using [Calendar Versioning](https://calver.org/) which means we need to manually specify new versions.
For example, to bump the version to November 8, 2024, you would run the following command after activating the relevant conda environment.

```bash
bump-my-version bump --new-version 2024.11.8
```

After releasing a new version, you need to push and include all tags.

```bash
git push --follow-tags
```

## License

All data, information, documentation, and associated content provided within this project are released under the [CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/deed.en) as specified in [`LICENSE`](https://github.com/durrantlab/molmoda-docs).
