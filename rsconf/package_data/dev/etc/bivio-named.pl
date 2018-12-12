{
    NamedConf => {
        hostmaster => 'hostmaster.bivio.biz.',
        servers => [qw(ns1.bivio.biz. ns2.bivio.biz.)],
        refresh => '1D',
        retry => '5M',
        expiry => '1W',
        # Cache time of negative responses
        minimum => '5M',
        ttl => '5M',
        mx_pref => 10,
        zones => {
            'radia.run' => {
                ipv4 => {
                    '10.10.10.0/24' => {
                        10 => 'v.radia.run',
                    },
                },
            },
        },
    },
}
