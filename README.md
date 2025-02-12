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

- AR: GobEnergy (http://datos.energia.gob.ar/dataset/precios-en-surtidor/archivo/80ac25de-a44a-4445-9215-090cf55cfda5)
- AT: Spritpreisrechner (https://www.spritpreisrechner.at/)
- AU: FuelWatch (https://www.fuelwatch.wa.gov.au), FuelSnoop (https://www.fuelsnoop.com.au/) and PetrolSpy (https://petrolspy.com.au)
- BE: DirectLease TankService (https://directlease.nl/tankservice/) - Use Netherlands data source below to access.
- BR: GasPass - Via proxy service hosted at https://gaspassproxy2-dhf8a6aphxbng9g4.brazilsouth-01.azurewebsites.net (you can host this yourself too)
- CA: GasBuddy (https://www.gasbuddy.com/) - Use US data source below to access.
- CH: Comparis (https://www.comparis.ch/benzin-preise)
- DE: TankerKoenig (https://tankerkoenig.de/)
- GB: CMA Temporary Road Fuel Price ODS (https://www.gov.uk/guidance/access-fuel-price-data), PodPoint Public Charges
- GR: FuelGR (https://fuelgr.gr/)
- NL: DirectLease TankService (https://directlease.nl/tankservice/)
- NZ: PetrolSpy (https://petrolspy.com.au) - Use Australia fuel source above to access.
- RO: Peco-Online (https://www.peco-online.ro/)
- SI: Goriva (https://goriva.si/)
- US: GasBuddy (https://www.gasbuddy.com/)

## Development

```bash
# Get a comprehensive list of development tools
just --list
```
