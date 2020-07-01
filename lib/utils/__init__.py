

def get_approximate_tax_for_retail(incl_tax,  excl_tax, retail_rate):
    """
    excl_tax    retail_rate
    -------- = -------------
    incl_tax    retail_rate_with_tax
    """

    return (incl_tax * retail_rate) / excl_tax





