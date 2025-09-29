import xarray as xr

ds = xr.open_dataset('tempsal.nc')
print('Dimensions:', ds.dims)
print('TAXIS size:', len(ds.TAXIS))
print('XAXIS size:', len(ds.XAXIS))
print('YAXIS size:', len(ds.YAXIS))
print('ZAX size:', len(ds.ZAX))
print('TAXIS range:', ds.TAXIS.values[0], 'to', ds.TAXIS.values[-1])
print('XAXIS range:', ds.XAXIS.values[0], 'to', ds.XAXIS.values[-1])
print('YAXIS range:', ds.YAXIS.values[0], 'to', ds.YAXIS.values[-1])
print('ZAX range:', ds.ZAX.values[0], 'to', ds.ZAX.values[-1])
