"""
The module to generate the csv files for TorStatus.

There is one function for each link.
"""
# Django-specific import statements -----------------------------------
from django.http import HttpResponse
from django.db.models import Max, Sum

# CSV specific import statements
import csv

# TorStatus specific import statements --------------------------------
from statusapp.models import ActiveRelay, Statusentry, Descriptor
from helpers import *

def current_results_csv(request):
    """
    Reformats the current Queryset object into a csv format.

    @rtype: HttpResponse
    @return: csv formatted current queryset
    """
    # Get the current columns from the session.
    current_columns = request.session['currentColumns']

    # Remove columns from which we don't want data.
    for obj in ['Hostname', 'Icons', 'Valid', 'Running', 'Hibernating',
            'Named']:
        current_columns = __delete_if_in(obj, current_columns)

    # Perform the query.
    last_va = ActiveRelay.objects.aggregate(
              last=Max('validafter'))['last']
    active_relays = ActiveRelay.objects.filter(
                   validafter=last_va).order_by('nickname')

    # Get the query options.
    query_options = {}
    if (request.GET):
        if ('resetQuery' in request.GET):
            if ('queryOptions' in request.session):
                del request.session['queryOptions']
        else:
            query_options = request.GET
            request.session['queryOptions'] = query_options
    if (not query_options and 'queryOptions' in request.session):
            query_options = request.session['queryOptions']

    # Use method in helper functions to filter the query results.
    active_relays = filter_active_relays(active_relays, query_options)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;\
            filename=current_results.csv'

    # Initialize dictionaries to write csv Data.
    rows = {}
    headers = {}

    # Make columns keys to empty lists.
    for column in current_columns: rows[column] = []

    # Populates the row dictionary with all field values.
    for relay in active_relays:
        fields_access = [("Router Name", relay.nickname),
                ("Country Code", relay.country),
                ("Bandwidth", relay.bandwidthobserved),
                ("Uptime", relay.uptime),
                ("IP", relay.address),
                ("Fingerprint", relay.fingerprint),
                ("LastDescriptorPublished", relay.published),
                ("Contact", relay.contact),
                ("BadDir", relay.isbaddirectory),
                ("DirPort", relay.dirport), ("Exit", relay.isexit),
                ("Authority", relay.isauthority),
                ("Fast", relay.isfast), ("Guard", relay.isguard),
                ("V2Dir", relay.isv2dir),
                ("Platform", relay.platform),
                ("Stable", relay.isstable), ("ORPort", relay.orport),
                ("BadExit", relay.isbadexit)]
        for k, v in fields_access:
            if k in current_columns: rows[k].append(v)

    writer = csv.writer(response)
    writer = csv.DictWriter(response, fieldnames=current_columns)

    for column in current_columns: headers[column] = column
    writer.writerow(headers)

    for i in range(0, len(rows[current_columns[0]])):
        dict_row = {}
        for column in current_columns:
            dict_row[column] = rows[column][i]
        writer.writerow(dict_row)

    return response


def exits_or_ips(request, all_flag):
    """
    Returns a csv formatted file that contains either all Tor ip
        addresses or all Tor exit node ip addresses.

    @type all_flag: C{bool}
    @param all_flag: a variable that represents the clients
        desire to get all the ips or only the exit node ips from
        the Tor network.

    @rtype: C{HttpResponse}
    @return: csv formatted list of either all ip address or all
        exit node ip addresses.
    """

    # Performs the necessary query depending on what is requested
    if all_flag:
        last_va = ActiveRelay.objects.aggregate(
                  last=Max('validafter'))['last']
        active_relays = ActiveRelay.objects.filter(validafter=last_va)
    else:
        last_va = ActiveRelay.objects.aggregate(
                  last=Max('validafter'))['last']
        active_relays = ActiveRelay.objects.filter(
                        validafter=last_va, isexit=True)

    # Initialize list to hold ips and populates it.
    IPs = []
    for relay in active_relays:
        IPs.append(relay.address)

    # Creates the proper csv response type.
    if all_flag:
        response = HttpResponse(mimetype= 'text/csv')
        response['Content-Disposition'] = 'attachment; filename=all_ips.csv'
    else:
        response = HttpResponse(mimetype= 'text/csv')
        response['Content-Disposition'] = 'attachment; filename=all_exit_ips.csv'

    # Writes IP list to csv response file.
    writer = csv.writer(response)
    for ip in IPs:
        writer.writerow([ip])

    return response

def __delete_if_in(obj, lst):
    """
    Deletes an object from a list if and only if that object is in the
    list.

    @type obj: C{str}
    @param obj: The object to delete from the list.
    @type lst: C{list} of C{str}
    @param lst: The list to delete the object from.
    @rtype: C{list} of C{str}
    @return: The original list if the object is not a member of the
        list, the original list without the object otherwise.
    """
    if obj in lst:
        lst.remove(obj)
        return lst
    else:
        return lst
