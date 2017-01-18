import pytest
import datetime
import bark
import numpy as np
import pandas as pd
import os.path


def test_write_sampled_empty(tmpdir):
    with pytest.raises(TypeError):
        bark.write_sampled("test_sampled", sampling_rate=10, units="mV", 
                n_channels=10, dtype="int16")


def test_write_sampled(tmpdir):
    data = np.zeros((10,3),dtype="int16")
    params = dict(sampling_rate=30000, units="mV", unit_scale=0.025,
            extra="barley")
    dset = bark.write_sampled(os.path.join(tmpdir.strpath, "test_sampled"), data=data, **params)
    assert isinstance(dset, bark.SampledData)
    assert isinstance(dset.path, str)
    assert isinstance(dset.attrs, dict)
    assert isinstance(dset.data, np.memmap)


def test_read_sampled(tmpdir):
    test_write_sampled(tmpdir)  # create 'test_sampled'
    path = os.path.join(tmpdir.strpath, "test_sampled")
    assert os.path.exists(path)
    assert os.path.exists(path + ".meta")
    dset = bark.read_sampled(path)
    assert isinstance(dset, bark.SampledData)
    assert isinstance(dset.path, str)
    assert isinstance(dset.attrs, dict)
    assert isinstance(dset.data, np.memmap)
    assert np.allclose(np.zeros((10,3)), dset.data)
    assert np.allclose(dset.data.shape, (10, 3))

def test_write_events(tmpdir):
    path = os.path.join(tmpdir.strpath, "test_events")
    data = pd.DataFrame({'start': [0,1,2,3], 'stop': [1,2,3,4],
            'name': ['a','b','c','d']})
    events = bark.write_events(path, data, units='s')
    assert isinstance(events, bark.EventData)
    assert 'start' in events.data.columns
    assert 'stop' in events.data.columns
    assert 'name' in events.data.columns
    assert np.allclose([0, 1, 2, 3], events.data.start)

def test_read_dataset(tmpdir):
    path = os.path.join(tmpdir.strpath, 'test_events')
    data = pd.DataFrame({'start': [0,1,2,3], 'stop': [1,2,3,4],
                         'name': ['a', 'b', 'c', 'd']})
    event_written = bark.write_events(path, data, units='s')
    event_read = bark.read_dataset(path)
    assert event_read.attrs['units'] == 's'
    assert event_read.attrs['datatype'] == 1000
    assert event_read.attrs['datatype_name'] == 'EVENT'
    
    path = os.path.join(tmpdir.strpath, 'test_samp')
    data = np.zeros((10,3),dtype="int16")
    params = {'sampling_rate': 30000, 'units' = 'mV', 'unit_scale': 0.025}
    samp_written = bark.write_sampled(path, data=data, **params)
    samp_read = bark.read_dataset(path)
    assert samp_read.attrs['units'] == params['units']
    assert samp_read.attrs['datatype'] == 0
    assert samp_read.attrs['datatype_name'] == 'UNDEFINED

def test_create_root(tmpdir):
    path = os.path.join(tmpdir.strpath, "mybark")
    root = bark.create_root(path, experimenter="kjbrown",
            experiment="testbark")
    assert isinstance(root, bark.Root)
    assert root.attrs["experimenter"] == "kjbrown"
    assert root.attrs["experiment"] == "testbark"

def test_create_entry(tmpdir):
    path = os.path.join(tmpdir.strpath, "myentry")
    dtime = datetime.datetime(2020,1,1,0,0,0,0)
    entry = bark.create_entry(path, dtime, food="pizza")
    assert 'uuid' in entry.attrs
    assert dtime == bark.timestamp_to_datetime(entry.attrs["timestamp"])
    assert entry.attrs["food"] == "pizza"

def test_entry_sort(tmpdir):
    path1 = os.path.join(tmpdir.strpath, "myentry")
    dtime1 = datetime.datetime(2020,1,1,0,0,0,0)
    entry1 = bark.create_entry(path1, dtime1, food="pizza")
    path2 = os.path.join(tmpdir.strpath, "myentry2")
    dtime2 = datetime.datetime(2021,1,1,0,0,0,0)
    entry2 = bark.create_entry(path2, dtime2, food="pizza")
    mylist = sorted([entry2, entry1])
    assert mylist[0] == entry1
    assert mylist[1] == entry2

def test_datatypes():
    assert bark.DataTypes.is_timeseries(0)
    assert bark.DataTypes.is_timeseries(1)
    assert (not bark.DataTypes.is_timeseries(1000))
    assert (not bark.DataTypes.is_timeseries(2002))
    assert bark.DataTypes.is_pointproc(1000)
    assert bark.DataTypes._fromstring('UNDEFINED') == 0
    assert bark.DataTypes._fromstring('EVENT') == 1000
    assert bark.DataTypes._fromcode(1) == 'ACOUSTIC'
    assert bark.DataTypes._fromcode(2002) == 'COMPONENTL"

def test__enforce_units():
    params = {'units': 'seconds'}
    bark._enforce_units(params)
    assert params['units'] == 's'
    params['units'] = 'samples'
    bark._enforce_units(params)
    assert params['units'] == 'samples'

def test__enforce_datatypes():
    params = {'datatype': 2}
    bark._enforce_datatypes(params) # should do nothing

    params['datatype'] = -1
    with pytest.raises(KeyError):
        bark._enforce_datatypes(params)

    params = {'units': 's'}
    bark._enforce_datatypes(params)
    assert params['datatype'] == 1000
    assert params['datatype_name'] == 'EVENT'
    
    params = {'units': 'mV'}
    bark._enforce_datatypes(params)
    assert params['datatype'] == 0
    assert params['datatype'] == 'UNDEFINED'

def test_dset_type_checkers(tmpdir):
    data = np.zeros((10,3),dtype="int16")
    params = dict(sampling_rate=30000, units="mV", unit_scale=0.025,
            extra="barley")
    samp = bark.write_sampled(os.path.join(tmpdir.strpath, "test_sampled"), data=data, **params)
    assert bark.is_sampled(samp)
    assert (not bark.is_events(samp))

    path = os.path.join(tmpdir.strpath, "test_events")
    data = pd.DataFrame({'start': [0,1,2,3], 'stop': [1,2,3,4],
            'name': ['a','b','c','d']})
    events = bark.write_events(path, data, units='s')
    assert (not bark.is_sampled(events))
    assert bark.is_events(events)