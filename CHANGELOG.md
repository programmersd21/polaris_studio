# Changelog

All notable changes to Polaris Studio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-06-08

### Changed
- **Chart rendering engine**: Replaced `pyqtgraph` with `matplotlib` for all chart types
  - Fixes STATUS_ACCESS_VIOLATION crashes on Windows with PySide6 6.10+
  - More stable rendering with better cross-platform compatibility
  - Improved chart export quality (PNG, SVG)
- Updated dependencies:
  - Removed: `pyqtgraph==0.13.3`
  - Added: `matplotlib>=3.8.0`

### Fixed
- Fixed crash when rendering bar charts with categorical x-axis labels
- Fixed animation lifecycle issues causing node state inconsistencies
- Chart rendering now deferred to clean event loop tick via `QTimer.singleShot(0)`
- `set_computing(False)` properly called in `_on_compute_finished` to stop animations

### Added
- Windows SEH crash diagnostics with minidump logging (`crash_<pid>.log`)
- Cinematic startup animation with icon and wordmark fade-in
- Full-window intro overlay that morphs to toolbar position

## [1.0.1] - 2026-06-07

### Fixed
- Animation cleanup and lifecycle management

## [1.0.0] - 2026-06-06

### Added
- Initial release of Polaris Studio
- Node-based data pipeline builder with visual graph editor
- CSV, Excel, Parquet, JSON file support
- Transform, filter, join, aggregate, and chart nodes
- AI assistant for pipeline generation (Google Gemini)
- Live spreadsheet with formula bar and column statistics
- Multi-tab workspace with save/load functionality
- Dark theme with Instrument Serif and Inter typography
