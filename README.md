<div align="center">

# pyfuelprices

A generic python module to retrieve fuel prices for different fuel suppliers.

[![Build Status](https://github.com/pantherale0/pyfuelprices/workflows/build/badge.svg)](https://github.com/pantherale0/pyfuelprices/actions)
[![Coverage Status](https://coveralls.io/repos/github/pantherale0/pyfuelprices/badge.svg?branch=main)](https://coveralls.io/github/pantherale0/pyfuelprices?branch=main)
[![PyPi](https://img.shields.io/pypi/v/pyfuelprices)](https://pypi.org/project/pyfuelprices)
[![Licence](https://img.shields.io/github/license/pantherale0/pyfuelprices)](LICENSE)

</div>

## Install

```bash
# Install tool
pip3 install pyfuelprices

# Install locally
just install
```

## Usage

TODO

## Datasources

Sources used to provide data for this module include:

- AU: FuelWatch (https://www.fuelwatch.wa.gov.au)
- AT: Spritpreisrechner (https://www.spritpreisrechner.at/)
- BE: DirectLease TankService (https://directlease.nl/tankservice/) - Use Netherlands data source below to access.
- DE: TankerKoenig (https://tankerkoenig.de/)
- GB: CMA Temporary Road Fuel Price ODS (https://www.gov.uk/guidance/access-fuel-price-data)
- NL: DirectLease TankService (https://directlease.nl/tankservice/)
- US: GasBuddy (https://www.gasbuddy.com/)

## Development

```bash
# Get a comprehensive list of development tools
just --list
```
