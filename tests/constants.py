from re import compile, IGNORECASE

VCR_REQUESTS_DISABLED_REGEX = compile(
    "No match for the request \\((<[^>]+>)\\) was found\\."
    " Can't overwrite existing cassette \\('none'\\) in your current record mode \\('none'\\)\\."
)

UUID_REGEX = compile(
    '[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', IGNORECASE
)
