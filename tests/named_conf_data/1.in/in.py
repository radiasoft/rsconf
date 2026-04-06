net1 = '111.22.33.24/29'
net2 = '2.3.4.24/29'

RESULT = {
    'expiry': '5M',
    'hostmaster': 'hostmaster.example.com.',
    'minimum': '6M',
    'mx_pref': 10,
    'servers': ['ns1.bivio.biz.', 'ns2.bivio.biz.'],
    'refresh': '7M',
    'retry': '8M',
    'spf1': 'include:aspmx.googlemail.com',
    'ttl': '9M',
    'nets': {
        '24-31.33.22.111': net1,
    },
    'zones': {
        'example.com': {
            'ipv4': {
                net1: {
                    24: [
                        '@mail',
                        'ns1',
                        ['example.com.', {
                            'spf1': '+ include:mail.yahoo.com',
                            'mx': [
                                'mail',
                                ['mail.other.com.', 20],
                            ],
                        }],
                    ],
                    25: [
                        ['ns2', {'ptr': 1}],
                        'www',
                    ],
                    26: 'two.level',
                },
                '10.10.1.0/29': {
                    1: 'ski',
                },
                '192.168.128.0/17': {
                    '182.16': [
                        'back',
                    ],
                },
            },
            'cname': {
                'ftp': 'www',
                'alias': 'example.other.com.',
            },
            'dkim1': {
                'mydkimhost._domainkey': 'PXWifNHWcbJ8y/Q1AQAB',
            },
            'txt': {
                'key1': 'value1',
            },
        },
        'example2.com': {
            'txt': [
                ['@', 'key1=abc'],
                ['@', 'key2=123'],
            ],
            'ipv4': [
                [net1, 27], 'net1.27',
                [net2, 27], 'net2-27',
                [net2, 28], 'net2-28',
            ],
        },
    },
}
