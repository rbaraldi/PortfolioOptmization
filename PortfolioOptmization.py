﻿
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import pandas as pd
import numpy
import matplotlib.pyplot as plt


def init_data(dt_start, dt_end, symbols):
    c_dataobj = da.DataAccess('Yahoo')
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    # timestamp hours=16.
    dt_timeofday = dt.timedelta(hours=16)
    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)

    # Get data
    ldf_data = c_dataobj.get_data(ldt_timestamps, symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # Filling the data for NAN
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    return d_data


def calc_basic_sim_info(dt_start, dt_end, symbols, lf_allocations):
    d_data = init_data(dt_start, dt_end, symbols)


    na_price = d_data['close'].values
    na_normalized_price = na_price / na_price[0, :]
    na_allocated_price = na_normalized_price * lf_allocations
    na_daily_cumulative_val = numpy.apply_along_axis(numpy.sum, 1, na_allocated_price)

    na_rets = na_daily_cumulative_val.copy()
    tsu.returnize0(na_rets)

    return na_price, na_daily_cumulative_val, na_rets


def compare_portfolio(dt_start, dt_end, symbols, lf_allocations):
    na_price,  na_daily_cumulative_val, na_rets = calc_basic_sim_info(dt_start, dt_end, symbols, lf_allocations)

    spy_price, spy_daily_cumulative_val, spy_rets = calc_basic_sim_info(dt_start, dt_end, ['SPY'], [1.0])

    plt.clf()
    fig = plt.figure()
    fig.add_subplot(111)
    plt.plot(spy_daily_cumulative_val, alpha=0.4)
    plt.plot(na_daily_cumulative_val)
    ls_names = ['SPY', 'Portfolio']
    plt.legend(ls_names)
    plt.ylabel('Cumulative Returns')
    plt.xlabel('Trading Day')
    fig.autofmt_xdate(rotation=45)
    plt.savefig('Portfolio.pdf', format='pdf')


def simulate(dt_start, dt_end, symbols, lf_allocations):
    
    d_data = init_data(dt_start, dt_end, symbols)

    na_price = d_data['close'].values
    na_normalized_price = na_price / na_price[0, :]
    na_allocated_price = na_normalized_price * lf_allocations
    
    na_daily_cumulative_val = numpy.apply_along_axis(numpy.sum, 1, na_allocated_price)

    na_rets = na_daily_cumulative_val.copy()
    
    tsu.returnize0(na_rets)

    vol = numpy.std(na_rets)
    dailyRet = numpy.mean(na_rets)
    cumulativeRet = na_daily_cumulative_val[-1]
    i_trading_days = na_price.shape[0]
    sharpe = (numpy.sqrt(i_trading_days) * dailyRet) / vol

    return vol, dailyRet, sharpe, cumulativeRet


def main():
    # Example
    #symbols = ['AAPL', 'GLD', 'GOOG', 'XOM']

    # List of symbols
    #symbols = ['AAPL', 'GOOG', 'IBM', 'MSFT']
    #symbols = ['BRCM', 'ADBE', 'AMD', 'ADI']
    #symbols = ['BRCM', 'TXN', 'AMD', 'ADI']
    #symbols = ['BRCM', 'TXN', 'IBM', 'HNZ']
    symbols = ['C', 'GS', 'IBM', 'HNZ']
    
    # Start and End date of the charts
    dt_start = dt.datetime(2010, 1, 1)
    dt_end = dt.datetime(2010, 12, 31)

    lf_best_allocation = None
    best_output = (0, 0, 0, 0)

    # get all legal permutations
    all_allocation = generate_allocations(symbols)

    #range over all possible allocation permutations
    for an_allocation in all_allocation:
        vol, daily_ret, sharpe, cum_ret = simulate(dt_start, dt_end, symbols, an_allocation)
        if sharpe > best_output[2]:
            best_output = (vol, daily_ret, sharpe, cum_ret)
            lf_best_allocation = an_allocation

    print "Start Date: {0:%B %d, %Y}".format(dt_start)
    print "End Date: {0:%B %d, %Y}".format(dt_end)
    print "Symbols: {0}".format(symbols)
    print "Optimal Allocations: {0}".format(lf_best_allocation)
    print "Sharpe Ratio: {0}".format(best_output[2])
    print "Volatility (stdev of daily returns): {0}".format(best_output[0])
    print "Average Daily Return: {0}".format(best_output[1])
    print "Cumulative Return: {0}".format(best_output[3])

    compare_portfolio(dt_start, dt_end, symbols, lf_best_allocation)


def generate_allocations(symbols):
    # list of possible allocations
    lf_range = numpy.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

    lf_lists = []

    for symbol in symbols:
        #one range per symbol in list
        lf_lists.append(lf_range.copy())

    lf_all = cartesian(lf_lists)

    #accumulator for legal allocations
    all_allocation = []

    #validate each allocation
    for an_allocation in lf_all:
        #adds up to 1?
        if numpy.sum(an_allocation) == 1:
            all_allocation.append(an_allocation)

    return all_allocation


def cartesian(arrays, out=None):
    """
    Generate a cartesian product of input arrays.

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])

    """

    arrays = [numpy.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = numpy.prod([x.size for x in arrays])
    if out is None:
        out = numpy.zeros([n, len(arrays)], dtype=dtype)

    m = n / arrays[0].size
    out[:, 0] = numpy.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m, 1:])
        for j in xrange(1, arrays[0].size):
            out[j * m:(j + 1) * m, 1:] = out[0:m, 1:]
    return out


if __name__ == '__main__':
    main()
