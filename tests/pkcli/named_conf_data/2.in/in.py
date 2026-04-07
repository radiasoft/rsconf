net1 = '1.2.3.0/24'

RESULT = {
    'expiry': '5M',
    'hostmaster': 'hostmaster.example.com.',
    'minimum': '6M',
    'mx_pref': 10,
    'servers': ['ns1.bivio.biz.', 'ns2.bivio.biz.'],
    'refresh': '7M',
    'retry': '8M',
    'ttl': '9M',
    'zones': {
        'example.com': {
            'ipv4': {
                net1: {
                    1: [
                        'no-dkim',
                        'dkim',
                        'dkim.multi.level',
                    ],
                    2: [
                        ['example.com.', {
                            'spf1': '1.2.3.10',
                        }],
                    ],
                },
            },
        },
        'example2.com': {
            'ipv4': {
                net1: {
                    3: [
                        'no-dkim',
                        'dkim',
                    ],
                },
            },
            'txt': [
                ['dkim', 'key1=abc'],
            ],
        },
    },
}