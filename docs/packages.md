
# How to build new package
1. Create new package

```shell
agio pkg new pkgname
```

2. Implement source code
3. Register the package in agio database

```shell
agio pkg register
```

4. Build the `whl` for test

```shell
agio pkg build
```

5. Make the new release

Provide a GitHub token with permissions to create releases.
Use environment variable `AGIO_GIT_REPOSITORY_TOKEN` or flag `-t`
```shell
export AGIO_GIT_REPOSITORY_TOKEN=github_pat_......
agio pkg release
```
