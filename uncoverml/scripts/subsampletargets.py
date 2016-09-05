
from random import sample
import os.path

import shapefile
import click

import uncoverml.logging


@click.command()
@click.argument('filename')
@click.option('-n', '--npoints', type=int, default=1000,
              help='Number of points to keep')
@click.option('-v', '--verbosity',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='Level of logging')
@click.option('-o', '--outputdir', default='.', help='Location to output file')
def cli(outputdir, npoints, verbosity, filename):

    # Setup the logging
    uncoverml.logging.configure(verbosity)
    name = os.path.basename(filename).rsplit(".", 1)[0]

    # Read the shapefile
    file = shapefile.Reader(filename)
    shapes = file.shapes()
    records = file.records()
    items = list(zip(shapes, records))

    # Randomly sample the shapefile to keep n points
    remaining_items = sample(items, npoints)

    # Create a new shapefile using the data saved
    w = shapefile.Writer(shapefile.POINT)
    w.fields = list(file.fields)
    keep_shapes, _ = zip(*items)
    for shape, record in remaining_items:
        w.records.append(record)
    w._shapes.extend(keep_shapes)

    # Write out the
    outfile = os.path.join(outputdir, name + '_' + str(npoints))
    w.save(outfile)
