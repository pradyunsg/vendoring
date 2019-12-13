# vendoring

A command line tool, to simplify vendoring pure Python dependencies.

## Why?

pip had a "home-grown" setup for vendoring dependencies. The `invoke` task grew in complexity to over 500 lines and, at some point, became extremely difficult to improve and maintain.

This tool is based off the overgrown `invoke` task, breaking it out into a dedicated codebase with the goal of making it more maintainable and reusable. This also enabled independent evolution of this codebase and better access to infrastructure (like dedicated CI) to ensure it keeps working properly.

## Contributing

Check the [Contributing](CONTRIBUTING.md) guide.
