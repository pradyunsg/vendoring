# vendoring

A command line tool, to simplify vendoring pure Python dependencies.

## Why does this exist?

pip had a "home-grown" setup for vendoring dependencies. The `invoke` task grew in complexity to over 500 lines and, at some point, became extremely difficult to improve and maintain.

This tool is based off the overgrown `invoke` task, breaking it out into a dedicated codebase with the goal of making it more maintainable and reusable. This also enabled independent evolution of this codebase and better access to infrastructure (like dedicated CI) to ensure it keeps working properly.

## Should I use it?

As a general rule of thumb, if the project is going to be a PyPI package, it should not use this tool.

Many downstream redistributors have policies against this kind of bundling of dependencies, which means that they'll patch your software to debundle it. This can cause various kinds of issues, due to violations of assumptions being made about where the dependencies are available/which versions are being used. These issues result in difficult-to-debug errors, which are fairly difficult to communicate with end users.

pip is a _very_ special case with a [thorough rationale][rationale] for
vendoring/bundling dependencies with itself.

[rationale]: https://pip.pypa.io/en/latest/development/vendoring-policy/#rationale

## Contributing

Check the [Contributing](CONTRIBUTING.md) guide.
