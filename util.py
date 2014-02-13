import optparse


def parse_options(options, flag_options=None, description=None, usage=None,
                  version=None):
    parser = optparse.OptionParser(description=description, usage=usage,
                                   version=version)
    for option, description in options.items():
        shortopt = '-%s' % (option)
        longopt = '--%s' % (description.split(';')[0])
        keyname = description.split(';')[0]
        help = ''
        if len(description.split(';')) > 1:
            help = description.split(';')[1]
        parser.add_option(shortopt, longopt, dest=keyname, help=help)
    if flag_options:
        for option, description in flag_options.items():
            shortopt = '-%s' % (option)
            longopt = '--%s' % (description.split(';')[0])
            keyname = description.split(';')[0]
            help = ''
            if len(description.split(';')) > 1:
                help = description.split(';')[1]
            parser.add_option(shortopt, longopt, dest=keyname,
                              action="store_true", help=help)
    (options, args) = parser.parse_args()
    return options

def generate_fqdn_and_pqdn(host):
    if host.endswith('.'):
        return (host, host[:-1])
    return ("%s." % host, host)
