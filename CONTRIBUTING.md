# Contributing

Thank you for your interest in contributing to vendoring. We welcome all
contributions and greatly appreciate your effort!

## Bugs and Feature Requests

If you have found any bugs or would like to request a new feature, please do
check if there is an existing issue already filed for the same, in the
project's GitHub [issue tracker]. If not, please file a new issue.

If you want to help out by fixing bugs, choose an open issue in the [issue
tracker] to work on and claim it by posting a comment saying "I would like to
work on this.". Feel free to ask any doubts in the issue thread.

While working on implementing the feature, please go ahead and file a pull
request. Filing a pull request early allows for getting feedback as early as
possible.

[issue tracker]: https://github.com/pradyunsg/vendoring/issues

## Pull Requests

Pull Requests should be small to facilitate easier review. Keep them
self-contained, and limited in scope. Studies have shown that review quality
falls off as patch size grows. Sometimes this will result in many small PRs to
land a single large feature.

Checklist:

1. All pull requests _must_ be made against the `master` branch.
2. Include tests for any functionality you implement. Any contributions helping
   improve existing tests are welcome.
3. Update documentation as necessary and provide documentation for any new
   functionality.

## Code Convention

This codebase uses the following tools for enforcing a code convention:

- [black] for code formatting
- [isort] for import sorting
- [mypy] for static type checking

To ease workflows, [pre-commit] is used to simplify invocation and usage of
these tools. To run all these tools on the codebase, run:

```sh-session
pre-commit run --all-files
```

[black]: https://github.com/psf/black
[isort]: https://github.com/timothycrosley/isort
[mypy]: https://github.com/python/mypy
[pre-commit]: https://pre-commit.com/
