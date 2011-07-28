"""
Helper functions for views.csvs, views.graphs, and views.pages.
"""
# General import statements -------------------------------------------
import datetime

# Django-specific import statements -----------------------------------
from django.http import HttpRequest
from django.http import HttpResponse

# Matplotlib-specific import statements -------------------------------
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

# TorStatus-specific import statements --------------------------------
from statusapp.models import Bwhist

# INIT Variables ------------------------------------------------------
COLUMN_VALUE_NAME = {'Country Code': 'country',
                     'Router Name': 'nickname',
                     'Bandwidth': 'bandwidthobserved',
                     'Uptime': 'uptime',
                     'IP': 'address',
                     'Hostname': 'hostname',
                     'Icons': 'icons',
                     'ORPort': 'orport',
                     'DirPort': 'dirport',
                     'BadExit': 'isbadexit',
                     'Named': 'isnamed',
                     'Exit': 'isexit',
                     'Authority': 'isauthority',
                     'Fast': 'isfast',
                     'Guard': 'isguard',
                     'Hibernating': 'ishibernating',
                     'Stable': 'isstable',
                     'Running': 'isrunning',
                     'Valid': 'isvalid',
                     'V2Dir': 'isv2dir',
                     'Platform': 'platform',
                     'Fingerprint': 'fingerprint',
                     'LastDescriptorPublished': 'published',
                     'Contact': 'contact',
                     'BadDir': 'isbaddirectory',
                    }

NOT_COLUMNS = ['Running', 'Hostname', 'Named', 'Valid',]

ICONS = ['Hibernating', 'Fast', 'Exit', 'V2Dir', 'Guard', 'Stable',
         'Authority', 'Platform',]


def filter_active_relays(active_relays, query_options):
    """
    Helper function that gets a QuerySet of ActiveRelays and a
    dictionary of search query options and filters the QuerySet
    based on this dictionary.

    @type active_relays: C{QuerySet}
    @param active_relays: A QuerySet of the active relays.
    @type query_options: C{dict}
    @param query_options: A list of the columns that will be displayed
        in this session.
    @rtype: QuerySet
    @return: statusentries
    """
    options = ['isauthority', 'isbaddirectory', 'isbadexit', \
               'isexit', 'isfast', 'isguard', 'ishibernating',
               'isnamed', 'isstable', 'isrunning', 'isvalid', 'isv2dir']
    # options is needed because query_options has some other things
    # that we do not need in this case (the other search query
    # key-values).
    valid_options = filter(lambda k: query_options[k] != '' \
                            and k in options, query_options)
    filterby = {}
    for opt in valid_options:
        filterby[opt] = 1 if query_options[opt] == 'yes' else 0

    if 'searchValue' in query_options and \
                query_options['searchValue'] != '':
        value = query_options['searchValue']
        criteria = query_options['criteria']
        logic = query_options['boolLogic']

        options = ['nickname', 'fingerprint', 'country',
                   'published','hostname', 'address',
                   'orport', 'dirport']

        # Special case: the value if searching for uptime or
        # bandwidth and the criteria is not Contains
        if (criteria == 'uptime' or criteria == 'bandwidthobserved') and \
                logic != 'contains':
            value = int(value) * (86400 if criteria == 'uptime' else 1024)

        key = criteria

        if logic == 'contains':
            key = key + '__contains'
        elif logic == 'less':
            key = key + '__lt'
        elif logic == 'greater':
            key = key + '__gt'

        if (criteria == 'uptime' or criteria == 'bandwidthobserved') and \
                logic == 'equals':
            lower_value = value
            upper_value = lower_value + (86400 if criteria == 'uptime' else 1024)
            filterby[key + '__gt'] = lower_value
            filterby[key + '__lt'] = upper_value
        else:
            filterby[key] = value

    active_relays = active_relays.filter(**filterby)

    options = set(('nickname', 'fingerprint', 'country',
               'bandwidthobserved', 'uptime', 'published', 'hostname',
               'address', 'orport', 'dirport', 'platform',
               'isauthority', 'isbaddirectory', 'isbadexit', 'isexit',
               'isfast', 'isguard', 'ishibernating', 'isnamed',
               'isstable', 'isrunning', 'isvalid', 'isv2dir'))

    if 'sortListings' in query_options:
        selected_option = query_options['sortListings']
    else:
        selected_option = ''
    if selected_option in options:
        if query_options['sortOrder'] == 'ascending':
            active_relays = active_relays.order_by(selected_option)
        elif query_options['sortOrder'] == 'descending':
            active_relays = active_relays.order_by(
                            '-' + selected_option)
    return active_relays

def button_choice(request, button, field, current_columns,
        available_columns):
    """
    Helper function that manages the changes in the L{columnpreferences}
    arrays/lists.

    @type button: C{string}
    @param button: A string that indicates which button was clicked.
    @type field: C{string}
    @param field: A string that indicates from which preferences column
        was the corresponding value selected
        (ADD column, REMOVE column).
    @type current_columns: C{list}
    @param current_columns: A list of the columns that will be
        displayed on this session.
    @type available_columns: C{list}
    @param available_columns: A list of the columns that can be added
        to the current ones.
    @rtype: list(list(int), list(int), string)
    @return: column_lists
    """
    selection = request.GET[field]
    if (button == 'removeColumn'):
        available_columns.append(selection)
        current_columns.remove(selection)
    elif (button == 'addColumn'):
        current_columns.append(selection)
        available_columns.remove(selection)
    elif (button == 'upButton'):
        selection_pos = current_columns.index(selection)
        if (selection_pos > 0):
            aux = current_columns[selection_pos - 1]
            current_columns[selection_pos - 1] = \
                           current_columns[selection_pos]
            current_columns[selection_pos] = aux
    elif (button == 'downButton'):
        selection_pos = current_columns.index(selection)
        if (selection_pos < len(current_columns) - 1):
            aux = current_columns[selection_pos + 1]
            current_columns[selection_pos + 1] = \
                           current_columns[selection_pos]
            current_columns[selection_pos] = aux
    request.session['currentColumns'] = current_columns
    request.session['availableColumns'] = available_columns
    column_lists = []
    column_lists.append(current_columns)
    column_lists.append(available_columns)
    column_lists.append(selection)
    return column_lists


def is_ip_in_subnet(ip, subnet):
    """
    Return True if the IP is in the subnet, return False otherwise.

    This implementation uses bitwise arithmetic and operators on
    subnets.

    >>> is_ip_in_subnet('0.0.0.0', '0.0.0.0/8')
    True
    >>> is_ip_in_subnet('0.255.255.255', '0.0.0.0/8')
    True
    >>> is_ip_in_subnet('1.0.0.0', '0.0.0.0/8')
    False

    @type ip: C{string}
    @param ip: The IP address to check for membership in the subnet.
    @type subnet: C{string}
    @param subnet: The subnet that the given IP address may or may not
        be in.
    @rtype: C{boolean}
    @return: True if the IP address is in the subnet, false otherwise.

    @see: U{http://www.webopedia.com/TERM/S/subnet_mask.html}
    @see: U{http://wiki.python.org/moin/BitwiseOperators}
    """
    # If the subnet is a wildcard, the IP will always be in the subnet
    if (subnet == '*'):
        return True

    # If the subnet is the IP, the IP is in the subnet
    if (subnet == ip):
        return True

    # If the IP doesn't match and no bits are provided, the IP is not
    # in the subnet
    if ('/' not in subnet):
        return False

    # Separate the base from the bits and convert the base to an int
    base, bits = subnet.split('/')

    # a.b.c.d becomes a*2^24 + b*2^16 + c*2^8 + d
    a, b, c, d = base.split('.')
    subnet_as_int = (int(a) << 24) + (int(b) << 16) + (int(c) << 8) + \
                     int(d)

    # Example: if 8 bits are specified, then the mask is calculated by
    # taking a 32-bit integer consisting of 1s and doing a bitwise shift
    # such that only 8 1s are left at the start of the 32-bit integer
    if (int(bits) == 0):
        mask = 0
    else:
        mask = (~0 << (32 - int(bits)))

    # Calculate the lower and upper bounds using the mask.
    # For example, 255.255.128.0/16 should have lower bound 255.255.0.0
    # and upper bound 255.255.255.255. 255.255.128.0/16 is the same as
    # 11111111.11111111.10000000.00000000 with mask
    # 11111111.11111111.00000000.00000000. Then using the bitwise and
    # operator, the lower bound would be
    # 11111111.11111111.00000000.00000000.
    lower_bound = subnet_as_int & mask

    # Similarly, ~mask would be 00000000.00000000.11111111.11111111,
    # so ~mask & 0xFFFFFFFF = ~mask & 11111111.11111111.11111111.11111111,
    # or 00000000.00000000.11111111.11111111. Then
    # 11111111.11111111.10000000.00000000 | (~mask % 0xFFFFFFFF) is
    # 11111111.11111111.11111111.11111111.
    upper_bound = subnet_as_int | (~mask & 0xFFFFFFFF)

    # Convert the given IP to an integer, as before.
    a, b, c, d = ip.split('.')
    ip_as_int = (int(a) << 24) + (int(b) << 16) + (int(c) << 8) + int(d)

    if (ip_as_int >= lower_bound and ip_as_int <= upper_bound):
        return True
    else:
        return False


def is_ipaddress(ip):
    """
    Return True if the given supposed IP address could be a valid IP
    address, False otherwise.

    >>> is_ipaddress('127.0.0.1')
    True
    >>> is_ipaddress('a.b.c.d')
    False
    >>> is_ipaddress('127.0.1')
    False
    >>> is_ipaddress('127.256.0.1')
    False

    @type ip: C{string}
    @param ip: The IP address to test for validity.
    @rtype: C{boolean}
    @return: True if the IP address could be a valid IP address,
        False otherwise.
    """
    # Including period separators, no IP as a string can have more than
    # 15 characters.
    if (len(ip) > 15):
        return False

    # Every IP must be separated into four parts by period separators.
    if (len(ip.split('.')) != 4):
        return False

    # Users can give IP addresses a.b.c.d such that a, b, c, or d
    # cannot be casted to an integer. If a, b, c, or d cannot be casted
    # to an integer, the given IP address is certainly not a
    # valid IP address.
    a, b, c, d = ip.split('.')
    try:
        if (int(a) > 255 or int(a) < 0 or int(b) > 255 or int(b) < 0 or
            int(c) > 255 or int(c) < 0 or int(d) > 255 or int(d) < 0):
            return False
    except:
        return False

    return True


def is_port(port):
    """
    Return True if the given supposed port could be a valid port,
    False otherwise.

    >>> is_port('80')
    True
    >>> is_port('80.5')
    False
    >>> is_port('65536')
    False
    >>> is_port('foo')
    False

    @type port: C{string}
    @param port: The port to test for validity.
    @rtype: C{boolean}
    @return: True if the given port could be a valid port, False
        otherwise.
    """
    # Ports must be integers and between 0 and 65535, inclusive. If the
    # given port cannot be casted as an int, it cannot be a valid port.
    try:
        if (int(port) > 65535 or int(port) < 0):
            return False
    except ValueError:
        return False

    return True


def port_match(dest_port, port_line):
    """
    Find if a given port number, as a string, could be defined as "in"
    an expression containing characters such as '*' and '-'.

    >>> port_match('80', '*')
    True
    >>> port_match('80', '79-81')
    True
    >>> port_match('80', '80')
    True
    >>> port_match('80', '443-9050')
    False

    @type dest_port: C{string}
    @param dest_port: The port to test for membership in port_line
    @type port_line: C{string}
    @param port_line: The port_line that dest_port is to be checked for
        membership in. Can contain * or -.
    @rtype: C{boolean}
    @return: True if dest_port is "in" port_line, False otherwise.
    """
    if (port_line == '*'):
        return True

    if ('-' in port_line):
        lower_str, upper_str = port_line.split('-')
        lower_bound = int(lower_str)
        upper_bound = int(upper_str)
        dest_port_int = int(dest_port)

        if (dest_port_int >= lower_port and
            dest_port_int <= upper_port):
            return True

    if (dest_port == port_line):
        return True

    return False


def get_if_exists(request, title):
    """
    Process the HttpRequest provided to see if a value, L{title}, is
    provided and retrievable by means of a C{GET}.

    If so, the data itself is returned; if not, an empty string is
    returned.

    @see: U{https://docs.djangoproject.com/en/1.2/ref/request-response/
    #httprequest-object}

    @type request: HttpRequest object
    @param request: The HttpRequest object that contains metadata
        about the request.
    @type title: C{string}
    @param title: The name of the data that may be provided by the
        request.
    @rtype: C{string}
    @return: The data with L{title} referenced in the request, if it
        exists.
    """
    if (title in request.GET and request.GET[title]):
        return request.GET[title].strip()
    else:
        return ""


def sorting_link(sort_order, column_name):
    """
    Returns the proper URL after checking how the sorting is currently
    set up.

    @type sort_order: C{string}
    @param sort_order: A string - the type of order
        (ascending/descending).
    @type column_name: C{string}
    @param column_name: A string - the name of the column that is
                    currently ordering by.
    @rtype: C{string}
    @return The proper link for sorting the tables.
    """
    if sort_order == "ascending":
        return "/" + column_name + "_descending"
    return "/" + column_name + "_ascending"


def kilobytes_ps(bytes_ps):
    """
    Convert a bandwidth value in bytes to a bandwidth value in kilobytes

    @type bytes_ps: C{int}, C{float}, C{long}, or C{string}
    @param bytes_ps: The bandwidth value, in bps.
    @rtype: C{int}
    @return: The bandwidth value in kbps.
    """
    # As statusapp.views.details is written now, this value can
    # be None or an empty string sometimes.
    if (bytes_ps == '' or bytes_ps is None):
        return 0
    else:
        return int(bytes_ps) / 1024


def days(seconds):
    """
    Convert an duration in seconds to an uptime in days, rounding down.

    @type seconds: C{int}, C{float}, C{long}, or C{string}
    @param seconds: The duration in seconds.
    @rtype: C{int}
    @return: The duration in days.
    """
    # As statusapp.views.details is written now, this value can
    # be None or an empty string sometimes.
    if (seconds == '' or seconds is None):
        return 0
    else:
        return int(seconds) / 86400


def contact(rawdesc):
    """
    Get the contact information of a relay from its raw descriptor.

    It is possible that a relay will not publish any contact information.
    In this case, "No contact information given" is returned.

    @type rawdesc: C{string} or C{buffer}
    @param rawdesc: The raw descriptor of a relay.
    @rtype: C{string}
    @return: The contact information of the relay.
    """
    for line in str(rawdesc).split("\n"):
        if (line.startswith("contact")):
            contact_raw = line[8:]
            return contact_raw.decode('raw_unicode_escape')
    return "No contact information given"


def get_platform(platform):
    """
    Method that searches in the platform string for the corresponding
    platform name.

    @type platform: C{string}
    @param platform: A string, raw version of the platform of a relay.
    @rtype: C{string}
    @return: The cleaned version of the platform name.
    """
    # Dictionary of {NameInPlatform: NameOfTheIcon}
    supported_platforms = {'Linux': 'Linux',
                           'XP': 'WindowsXP',
                           'Windows Server': 'WindowsServer',
                           'Windows': 'WindowsOther',
                           'Darwin': 'Darwin',
                           'FreeBSD': 'FreeBSD',
                           'NetBSD': 'NetBSD',
                           'OpenBSD': 'OpenBSD',
                           'SunOS': 'SunOS',
                           'IRIX': 'IRIX',
                           'Cygwin': 'Cygwin',
                           'Dragon': 'DragonFly',
                          }
    if platform is None:
        return 'NotAvailable'
    for name in supported_platforms:
        if name in platform:
            return supported_platforms[name]
    return 'NotAvailable'


def generate_table_headers(current_columns, order_column_name, sort_order):
    """
    Generates a dictionary of {header_name: html_string_code}.

    @type current_columns: C{list}
    @param current_columns: A list of the columns that will be
        displayed on this session.
    @type order_column_name: C{string}
    @param order_column_name: A string - the name of the column that is
        currently ordering by.
    @type sort_order: C{string}
    @param sort_order: A string - the type of order
        (ascending/descending).
    @rtype: C{dict}, C{list}
    @return: Dictionary that contains the header name and the HTML code.
        List of the current columns that will be displayed.
    """
    # NOTE: The html_current_columns list is needed to preserve the order
    # of the displayed columns. It is used in the template to iterate
    # through the current columns in the right order that they should be
    # displayed.
    html_table_headers = {}
    html_current_columns = []
    for column in current_columns:
        database_name = COLUMN_VALUE_NAME[column]
        display_name = "&nbsp;&nbsp;" if column == "Country Code" else column
        sort_arrow = ''
        if order_column_name == database_name:
            if sort_order == 'ascending':
                sort_arrow = "&uarr;"
            elif sort_order == 'descending':
                sort_arrow = "&darr;"
        html_class = "relayHeader hoverable" if database_name != "icons" \
                                                else "relayHeader"

        if column not in ICONS and column not in NOT_COLUMNS:
            if column == "Icons":
                if filter(lambda c: c in current_columns, ICONS):
                    html_table_headers[column] = "<th class='" + html_class +\
                                        "' id='" \
                                        + database_name + "'>" + display_name +\
                                        "</th>"
                    html_current_columns.append(column)
            else:
                html_table_headers[column] = "<th class='" + html_class + \
                                    "' id='" + database_name + "'>\
                                    <a class='sortLink' href='" + \
                                    sorting_link(sort_order, database_name) \
                                    + "'>" + display_name + " " + sort_arrow +\
                                    "</a></th>"
                html_current_columns.append(column)
    return html_table_headers, html_current_columns


def generate_table_rows(active_relays, current_columns,
        html_current_columns):
    """
    Generates a list of HTML strings. Each string represents a row in
    the main template table.

    @type statusentries: C{QuerySet}
    @param statusentries: A QuerySet of the statusentries.
    @type current_columns: C{list}
    @param current_columns: A list of the columns that will be displayed
        on this session.
    @type html_current_columns: C{list}
    @param html_current_columns: A list of the HTML string version of
        the current columns.

    @rtype: C{list}
    @return: List of HTML strings.
    """
    html_table_rows = []

    for relay in active_relays:
        #TODO: CLEAN THE CODE - QUERY ONLY ON THE NECESSARY COLUMNS
        #               AND THROW IN DICTIONARY AFTERWARDS!!!
        # Declarations made in order to avoid multiple queries.
        r_isbadexit = relay.isbadexit
        field_isbadexit = "<img src='static/img/bg_" + \
                        ("yes" if r_isbadexit else "no") + \
                        ".png' width='12' height='12' alt='" + \
                        ("Bad Exit' title='Bad Exit'" \
                        if r_isbadexit else \
                        "Not a Bad Exit' title='Not a Bad Exit'") + ">"
        r_ishibernating = True if relay.ishibernating else False
        field_country = str(relay.country)
        field_latitude = str(relay.latitude)
        field_longitude = str(relay.longitude)
        field_isnamed = relay.isnamed
        field_fingerprint = relay.fingerprint
        field_nickname = relay.nickname
        field_bandwidthobserved = str(relay.bandwidthkbps) + ' KB/s'
        field_uptime = str(relay.uptimedays) + ' d'
        r_address = relay.address
        field_address = "[<a href='details/" + r_address + \
                        "/whois'>" + r_address + "</a>]"
        field_published = str(relay.published)
        field_contact = relay.contact
        r_isbaddir = relay.isbaddirectory
        field_isbaddirectory = "<img src='static/img/bg_" + \
                        ("yes" if r_isbaddir else "no") + \
                        ".png' width='12' height='12' alt='" + \
                        ("Bad Directory' title='Bad Directory'" \
                        if r_isbaddir else "Not a Bad Directory' \
                        title='Not a Bad Directory'") + ">"
        field_isfast = "<img src='static/img/status/Fast.png' \
                        alt='Fast Server' title='Fast Server'>" \
                        if relay.isfast else ""
        field_isv2dir = "<img src='static/img/status/Dir.png' \
                        alt='Directory Server' title='Directory Server'>" \
                        if relay.isv2dir else ""
        field_isexit = "<img src='static/img/status/Exit.png' \
                        alt='Exit Server' title='Exit Server'>" \
                        if relay.isexit else ""
        field_isguard = "<img src='static/img/status/Guard.png' \
                        alt='Guard Server' title='Guard Server'>" \
                        if relay.isguard else ""
        field_ishibernating = "<img src='static/img/status/Hibernating.png' \
                              alt='Hibernating Server' title= \
                              'Hibernating Server'" \
                              if r_ishibernating else ""
        field_isstable = "<img src='static/img/status/Stable.png' \
                        alt='Stable Server' title='Stable Server'>" \
                        if relay.isstable else ""
        field_isauthority = "<img src='static/img/status/Authority.png' \
                        alt='Authority Server' title='Authority Server'>" \
                        if relay.isauthority else ""
        r_platform = relay.platform if relay.platform else 'Not Available'
        r_os_platform = get_platform(r_platform)
        field_platform = "<img src='static/img/os-icons/" + r_os_platform + \
                        ".png' alt='" + r_os_platform + "' title='" + \
                        r_platform + "'>" if r_os_platform else ""
        field_orport = str(relay.orport)
        r_dirport = str(relay.dirport) if relay.dirport else "None"
        field_dirport = r_dirport if r_dirport else "None"


        RELAY_FIELDS = {'isbadexit': field_isbadexit,
                        'country': field_country,
                        'latitude': field_latitude,
                        'longitude': field_longitude,
                        'isnamed': field_isnamed,
                        'fingerprint': field_fingerprint,
                        'nickname': field_nickname,
                        'bandwidthobserved': field_bandwidthobserved,
                        'uptime': field_uptime,
                        'address': field_address,
                        'published': field_published,
                        'contact': field_contact,
                        'isbaddirectory': field_isbaddirectory,
                        'isfast': field_isfast,
                        'ishibernating': field_ishibernating,
                        'isv2dir': field_isv2dir,
                        'isexit': field_isexit,
                        'isguard': field_isguard,
                        'isstable': field_isstable,
                        'isauthority': field_isauthority,
                        'platform': field_platform,
                        'orport': field_orport,
                        'dirport': field_dirport,
                       }

        html_row_code = ''

        if 'isbadexit' in RELAY_FIELDS and r_isbadexit:
            html_row_code = "<tr class='relayBadExit'>"
        elif 'ishibernating' in RELAY_FIELDS and r_ishibernating:
            html_row_code = "<tr class='relayHibernating'>"
        else:
            html_row_code = "<tr class='relay'>"

        for column in html_current_columns:
            value_name = COLUMN_VALUE_NAME[column]

            # Special Case: Country Code
            if column == 'Country Code':
                c_country = RELAY_FIELDS[value_name]
                c_latitude = RELAY_FIELDS['latitude']
                c_longitude = RELAY_FIELDS['longitude']
                html_row_code = html_row_code + "<td id='col_relayName'> \
                                <a href='http://www.openstreetmap.org/?mlon="\
                                 + c_longitude + "&mlat=" + c_latitude + \
                                 "&zoom=6'><img src='static/img/flags/" + \
                                 c_country.lower() + ".gif' alt='" + c_country + \
                                 "' title='" + c_country + ":" + c_latitude +\
                                 ", " + c_longitude + "' border=0></a></td>"
            # Special Case: Router Name and Named
            elif column == 'Router Name':
                if 'Named' in current_columns:
                    html_router_name = "<a class='link' href='/details/" + \
                                        RELAY_FIELDS['fingerprint'] + "' \
                                        target='_BLANK'>" + \
                                        RELAY_FIELDS[value_name] + "</a>"
                    if RELAY_FIELDS['isnamed']:
                        html_router_name = "<b>" + html_router_name + "</b>"
                else:
                    html_router_name = "<a class='link' href='/details/" + \
                                        RELAY_FIELDS['fingerprint'] + "' \
                                        target='_BLANK'>" + \
                                        RELAY_FIELDS[value_name] + "</a>"
                html_row_code = html_row_code + "<td id='col_relayName'>"\
                                    + html_router_name + "</td>"
            # Special Case: Icons
            elif column == 'Icons':
                html_icons = "<td id='col_relayIcons'>"
                for icon in ICONS:
                    if icon in current_columns:
                        value_icon = COLUMN_VALUE_NAME[icon]
                        html_icons = html_icons + RELAY_FIELDS[value_icon]
                html_icons = html_icons + "</td>"
                html_row_code = html_row_code + html_icons
            else:
                html_row_code = html_row_code + "<td id='col_relay" + column \
                                + "'>" + RELAY_FIELDS[value_name] + "</td>"
        html_row_code = html_row_code + "</tr>"
        html_table_rows.append(html_row_code)

    return html_table_rows


def generate_query_list_options(query_options):
    """
    Generates the HTML version of each option in the Query List Options
    field.

    @type query_options: C{dict}
    @param query_options: A dictionary of the current query options.
    @rtype: C{list}
    @return: List of strings - each string represents the HTML version
        of an option.
    """
    # TODO: Finish this. It will clean up the
    # Advanced Query Options search.
    LIST_OPTIONS = {'Router Name': 'nickname',
                    'Fingerprint': 'fingerprint',
                    'Country Code': 'country',
                    'Bandwidth': 'bandwidthobserved',
                    'Uptime': 'uptime',
                    'Last Descriptor Published': 'published',
                    #'Hostname': 'hostname',
                    'IP Address': 'address',
                    'ORPort': 'orport',
                    'DirPort': 'dirport',
                    'Platform': 'platform',
                    'Contact': 'contact',
                    'Authority': 'isauthority',
                    'Bad Directory': 'isbaddirectory',
                    'Bad Exit': 'isbadexit',
                    'Exit': 'isexit',
                    'Fast': 'isfast',
                    'Guard': 'isguard',
                    'Hibernating': 'ishibernating',
                    'Named': 'isnamed',
                    'Stable': 'isstable',
                    'Valid': 'isvalid',
                    'Directory': 'isv2dir',
                   }
