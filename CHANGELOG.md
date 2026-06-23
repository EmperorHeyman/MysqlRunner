# Changelog

All notable changes to MySQL Runner are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/) and
[Semantic Versioning](https://semver.org/).

## [1.0.3] - 2026-06-23

### Changed
- **Dark mode rewritten.** Dropped the full-page `invert(1) hue-rotate()` CSS
  filter — which only produced a washed-out grey negative and miscoloured
  images — in favour of the bundled [Dark Reader](https://darkreader.org)
  engine. It reads each element's computed colours at runtime and generates
  proper dark equivalents (text, backgrounds, borders, images), watching the
  DOM for changes, so there are no more white-on-white elements or smudged
  fonts. The library is vendored under `mysql_runner/web/vendor/` and bundled
  into the build so dark mode works offline and inside the packaged `.exe`.

### Fixed
- Fixed dark mode failing with `ReferenceError: __PLUS__ is not defined` /
  `DarkReader.enable is not a function`, caused by a broken upstream Dark Reader
  release (4.9.108). Pinned to the clean 4.9.109 build.

## [1.0.2] - earlier

- See the project git history for changes prior to 1.0.3.
