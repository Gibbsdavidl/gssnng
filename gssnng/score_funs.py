import numpy as np
import gssnng.util as si
import statsmodels.robust.scale

def summed_up(su):
    """
    Just sum up the counts

    :param x: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    mad_su = statsmodels.robust.scale.mad(su)
    score = np.sum(su)
    return((score, mad_su))


def median_score(su):
    """
    Average Z score

    :param x: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    cnts_med = np.median(su)
    mad_su = statsmodels.robust.scale.mad(su)
    return((cnts_med, mad_su))


def average_score(su):
    """
    Average Z score

    :param x: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    cnts_mean = np.mean(su)
    std_su = np.std(su)
    return((cnts_mean, std_su))


def mean_z(exprdat, su):
    """
    Average Z score

    :param exprdat: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    vals_mean = np.mean(exprdat)
    vals_std = np.std(exprdat)
    centered = [ (np.abs(x - vals_mean) / vals_std) for x in su ]
    score = np.mean(centered)
    return((score, vals_std))


def robust_std(exprdat, su):
    """
    Median of median standardized counts

    :param exprdat: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    cnts_med = np.median(exprdat)
    mad_su = statsmodels.robust.scale.mad(exprdat)
    centered_cnts = [ (np.abs(x - cnts_med) / mad_su) for x in su ]
    score = np.median(centered_cnts)
    return((score, mad_su))


def rank_biased_overlap(x, su, gs, limit=100):
    """
    Rank biased overlap method

    :param x: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param gs: the gene set
    """

    rbo_score = 0.0

    y = su # should be the ranked values

    for i,gi in enumerate(gs):
        subrank = y[0:(i+1)]
        subset = set(subrank.index)
        rbo_score += len(subset.intersection(gs))
        if i > limit:
            break

    mad_up = statsmodels.robust.scale.mad(su)
    return((rbo_score, mad_up))


def singscore(x, su, sig_len, norm_method):
    """
    The singscore method

    :param x: the pandas data frame of ranks, all genes
    :param su: the ranked list of genes *IN* the gene set
    :param sig_len_up: the number of expressed genes matched in the set
    :param norm_method: 'standard or theoretical' # from singscore
    :param score_up: is the rank up or down?  True or False
    """
    # normalise the score for the number of genes in the signature
    score_up = np.mean(su)
    norm_up = si.normalisation(norm_method=norm_method,
                               library_len=len(x.index),
                               score_list=su,
                               score=score_up,
                               sig_len=sig_len)
    norm_up = norm_up - 0.5
    mad_up = statsmodels.robust.scale.mad(su)
    return((norm_up, mad_up))


def expr_format(x, exprdat, geneset_genes):
    sig_len_up = len(geneset_genes)
    su = []
    for j in geneset_genes:
        if j in x.index:
            su.append(exprdat[j])
        else:
            sig_len_up = sig_len_up - 1
    return( (su, sig_len_up) )


def method_selector(gs, x, exprdat, geneset_genes, method, method_params):
    """
    :param gs: the gene set
    :param x: the gene expr data frame
    :param exprdat: the values we'll compute on
    :param geneset_genes: genes in the gene set
    :param method: the method we'll call
    :param method_params: dictionary of method parameters
    :param barcode: cell barcode

    :return: dictionary of results
    """

    (su, sig_len) = expr_format(x, exprdat, geneset_genes)

    if method == 'singscore':
        res0 = singscore(exprdat, su, sig_len, method_params['normalization'])

    elif method == 'robust_std':
        res0 = robust_std(exprdat, su)

    elif method == 'summed_up':
        res0 = summed_up(su)

    elif method == 'median_score':
        res0 = median_score(exprdat, su)

    elif method == 'average_score':
        res0 = average_score(exprdat, su)

    elif method == 'mean_z':
        res0 = mean_z(exprdat, su)

    elif method == 'rank_biased_overlap':
        res0 = rank_biased_overlap(exprdat, su, gs, gs.mode, method_params['rbo_depth'])

    else:
        return("ERROR")

    return(res0)


def scorefun(gs,
             x,
             method,
             method_params,
             barcode,
             ranked):
    """
    given a ranked list, produce a score

    :param gs: the gene set
    :param x: the pandas data frame of ranks, all genes
    :param method: the method we'll call
    :param method_params: dictionary of method parameters
    :param barcode: cell barcode

    :return a tuple (a,b,c,d,e)  score is 'a', extra info is in 'b'
    """

    if (gs.mode == 'UP') and (ranked == False):
        res0 = method_selector(gs, x, x.counts, gs.genes_up, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode, score=res0[0], var=res0[1])

    elif (gs.mode == 'DN') and (ranked == False):
        res0 = method_selector(gs, x, x.counts, gs.genes_dn, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode, score=res0[0], var=res0[1])

    elif (gs.mode == 'BOTH') and (ranked == False):
        res0_up = method_selector(gs, x, x.counts, gs.genes_up , method, method_params)
        res0_dn = method_selector(gs, x, x.counts, gs.genes_dn, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode,
                    score=(res0_up[0]+res0_dn[0]), var=(res0_up[1]+res0_dn[1]))

    elif (gs.mode == 'UP') and (ranked == True):
        res0 = method_selector(gs, x, x.uprank, gs.genes_up, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode, score=res0[0], var=res0[1])

    elif (gs.mode == 'DN') and (ranked == True):
        res0 = method_selector(gs, x, x.dnrank, gs.genes_dn, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode, score=res0[0], var=res0[1])

    elif (gs.mode == 'BOTH') and (ranked == True):
        res0_up = method_selector(gs, x, x.uprank, gs.genes_up , method, method_params)
        res0_dn = method_selector(gs, x, x.dnrank, gs.genes_dn, method, method_params)
        res1 = dict(barcode = barcode, name=gs.name, mode=gs.mode,
                    score=(res0_up[0]+res0_dn[0]), var=(res0_up[1]+res0_dn[1]))

    return(res1)

