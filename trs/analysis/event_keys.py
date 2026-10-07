"""Shared SQL expressions for deterministic analytical event keys."""

# ACCNUM is populated for most KSI years, but the source contains the literal
# string ``None`` for nearly every 2015-2019 row.  The fallback fields describe
# the occurrence rather than an involved party, so party rows from the same
# event collapse to one stable key.
KSI_EVENT_KEY_SQL = """
case
    when "ACCNUM" is not null
         and lower(trim("ACCNUM")) not in ('', 'none', 'null', 'nan')
        then 'accnum:' || trim("ACCNUM")
    else concat(
        'fallback:',
        coalesce(trim("DATE"), ''), '|',
        coalesce(trim("TIME"), ''), '|',
        upper(coalesce(trim("STREET1"), '')), '|',
        upper(coalesce(trim("STREET2"), '')), '|',
        coalesce(trim("geometry"), '')
    )
end
""".strip()
