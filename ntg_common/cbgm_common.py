# -*- encoding: utf-8 -*-

"""Common routines for the CBGM.

"""

import collections
import logging

import networkx as nx
import numpy as np

from ntg_common import db_tools
from ntg_common.db_tools import execute, executemany, executemany_raw
from ntg_common.tools import log


class CBGM_Params ():
    """ Structure that holds intermediate results of the CBGM. """

    n_mss = 0
    "No. of manuscripts"

    n_passages = 0
    "No. of passages"

    n_ranges = 0
    "No. of ranges"

    ranges = None
    "list of (named tuple Range)"

    variant_matrix = None
    """Boolean (1 x passages) matrix of invariant passages.  We will need this the
    day we decide *not* to eliminate all invariant readings from the
    database.

    """

    labez_matrix = None
    """Integer matrix (mss x passages) of labez.  Each entry represents one reading:
    0 = lacuna, 1 = 'a', 2 = 'b', ...  Used by the pre-coherence computations.

    """

    def_matrix = None
    """Boolean matrix (mss x passages) set if ms. is defined at passage."""

    and_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages that are
    defined in both mss.

    """

    eq_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages that are
    equal in both mss.

    """

    parent_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages that are
    older in ms1 than in ms2, using only immediate descendence.  This matrix is
    asymmetrical.

    """

    ancestor_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages that are
    older in ms1 than in ms2.  This matrix is asymmetrical.

    """

    unclear_parent_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages whose
    relationship is unclear in ms1 and ms2, using only immediate descendence.

    """

    unclear_ancestor_matrix = None
    """Integer matrix (ranges x mss x mss) with counts of the passages whose
    relationship is unclear in ms1 and ms2.

    """


def create_labez_matrix (dba, parameters, val):
    """Create the :attr:`labez matrix <scripts.cceh.cbgm.CBGM_Params.labez_matrix>`."""

    with dba.engine.begin () as conn:

        np.set_printoptions (threshold = 30)

        # get passages
        res = execute (conn, """
        SELECT count (*)
        FROM passages
        """, parameters)
        val.n_passages = res.fetchone ()[0]

        # get matrix of invariant passages
        # Initialize all passages to 'variant'
        variant_matrix = np.ones ((1, val.n_passages), np.bool_)

        res = execute (conn, """
        SELECT pass_id - 1
        FROM passages
        WHERE NOT (variant)
        """, parameters)

        for row in res:
            variant_matrix [0, row[0]] = False
        val.variant_matrix = variant_matrix

        # get no. of manuscripts
        res = execute (conn, """
        SELECT count (*)
        FROM manuscripts
        """, parameters)
        val.n_mss = res.fetchone ()[0]

        # get no. of ranges
        Range = collections.namedtuple ('Range', 'rg_id range start end')
        res = execute (conn, """
        SELECT rg_id, range, MIN (pass_id) - 1 AS first_id, MAX (pass_id) AS last_id
        FROM ranges ch
        JOIN passages p ON ch.passage @> p.passage
        GROUP BY rg_id, range
        ORDER BY lower (ch.passage), upper (ch.passage) DESC
        """, parameters)
        val.n_ranges = res.rowcount
        val.ranges = list (map (Range._make, res))
        log (logging.INFO, '  No. of ranges: ' + str (val.n_ranges))

        # Matrix ms x pass

        # Initialize all manuscripts to the labez 'a'
        labez_matrix  = np.broadcast_to (np.array ([1], np.uint32), (val.n_mss, val.n_passages)).copy ()

        # overwrite matrix where actual labez is not 'a'
        res = execute (conn, """
        SELECT ms_id - 1, pass_id - 1, ord_labez (labez) as labez
        FROM apparatus a
        WHERE labez != 'a' AND cbgm
        """, parameters)

        for row in res:
            labez_matrix [row[0], row[1]] = row[2]

        # clear matrix where reading is uncertain
        res = execute (conn, """
        SELECT DISTINCT ms_id - 1, pass_id - 1
        FROM apparatus
        WHERE certainty != 1.0
        """, parameters)

        for row in res:
            labez_matrix [row[0], row[1]] = 0

        val.labez_matrix = labez_matrix

        # Boolean matrix ms x pass set where passage is defined
        val.def_matrix = np.greater (val.labez_matrix, 0)
        val.def_matrix = np.logical_and (val.def_matrix, val.variant_matrix) # mask invariant passages

        log (logging.INFO, '  Size of the labez matrix: ' + str (val.labez_matrix.shape))


def count_by_range (a, range_starts, range_ends):
    """Count true bits in array ranges

    Count the bits that are true in multiple ranges of the same array of booleans.

    :param numpy.Array a:      Input array
    :type a: np.Array of np.bool:
    :param int[] range_starts: Starting offsets of the ranges to count.
    :param int[] range_ends:   Ending offsets of the ranges to count.

    """
    cs = np.cumsum (a)    # cs[0] = a[0], cs[1] = cs[0] + a[1], ..., cs[n] = total
    cs = np.insert (cs, 0, 0)
    cs_start = cs[range_starts] # get the sums at the range beginnings
    cs_end   = cs[range_ends]   # get the sums at the range ends
    return cs_end - cs_start


def calculate_mss_similarity_preco (_dba, _parameters, val):
    r"""Calculate pre-coherence mss similarity

    The pre-coherence similarity is defined as:

    .. math::

        \mbox{similarity}=\frac{\mbox{equal passages}}{\mbox{passages in common}}

    ..

        Kapitelweise füllen auf Basis von Vergleichen einzelner
        Variantenspektren in ECM_Acts_Sp.  Vergleich von je zwei Handschriften:
        An wieviel Stellen haben sie gemeinsam Text, an wieviel Stellen stimmen
        sie überein bzw. unterscheiden sie sich (inklusive Quotient)?  Die
        Informationen werden sowohl auf Kapitel- wie auch Buchebene
        festgehalten.

        --VGA/VG05_all3.pl

    """

    # Matrix range x ms x ms with count of the passages that are defined in both mss
    val.and_matrix = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

    # Matrix range x ms x ms with count of the passages that are equal in both mss
    val.eq_matrix  = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

    val.range_starts = [ch.start for ch in val.ranges]
    val.range_ends   = [ch.end   for ch in val.ranges]

    # pre-genealogical coherence outputs symmetrical matrices
    # loop over all mss O(n_mss² * n_ranges * n_passages)

    for j in range (0, val.n_mss):
        labezj = val.labez_matrix[j]
        defj   = val.def_matrix[j]

        for k in range (j + 1, val.n_mss):
            labezk = val.labez_matrix[k]
            defk   = val.def_matrix[k]

            def_and  = np.logical_and (defj, defk)
            labez_eq = np.logical_and (def_and, np.equal (labezj, labezk))

            val.and_matrix[:,j,k] = val.and_matrix[:,k,j] = count_by_range (def_and, val.range_starts, val.range_ends)
            val.eq_matrix[:,j,k]  = val.eq_matrix[:,k,j]  = count_by_range (labez_eq, val.range_starts, val.range_ends)


def calculate_mss_similarity_postco (dba, parameters, val, do_checks = True):
    """Calculate post-coherence mss similarity

    Genealogical coherence outputs asymmetrical matrices.
    Loop over all mss O(n_mss² * n_ranges * n_passages).

    """

    with dba.engine.begin () as conn:

        # Load all passages into memory

        res = execute (conn, """
        SELECT pass_id, begadr, endadr FROM passages
        ORDER BY pass_id
        """, parameters)

        stemmas = dict ()
        for pass_id, begadr, endadr in res.fetchall ():
            G = db_tools.local_stemma_to_nx (conn, pass_id, True) # True == add isolated roots

            if do_checks:
                # sanity tests
                # connect the graph through a root node for the following tests:
                G.add_node ('root', label = 'root')
                G.add_edge ('root', '*')
                G.add_edge ('root', '?')
                if not nx.is_weakly_connected (G):
                    # use it anyway
                    log (logging.WARNING, "Local Stemma @ %s-%s is not connected (pass_id=%s)." %
                         (begadr, endadr, pass_id))
                if not nx.is_directed_acyclic_graph (G):
                    # don't use these
                    log (logging.ERROR, "Local Stemma @ %s-%s is not a directed acyclic graph (pass_id=%s)." %
                         (begadr, endadr, pass_id))
                    continue
                # ... and remove it again
                G.remove_node ('root')

            G.nodes['*']['mask'] = 0
            G.nodes['?']['mask'] = 1 # bitmask == 1 signifies source is unclear

            # build node bitmasks.  Every node gets a different bit set.
            i = 1
            for n in sorted (G.nodes ()):
                attrs = G.nodes[n]
                attrs['parents'] = 0
                attrs['ancestors'] = 0
                if 'mask' not in attrs:
                    i += 1
                    if i < 64:
                        attrs['mask'] = (1 << i)
                    else:
                        attrs['mask'] = 0
                        # mask is 64 bit only
                        log (logging.ERROR, "Too many cliques in local stemma @ %s-%s (pass_id=%s)." %
                             (begadr, endadr, pass_id))

            # build the parents bit mask. We set the bits of the parent nodes.
            for n in G:
                mask = G.nodes[n]['mask']
                for succ in G.successors (n):
                    G.nodes[succ]['parents'] |= mask

            # build the ancestors mask.  We set the bits of all node ancestors.
            TC = nx.transitive_closure (G)
            for n in TC:
                # transitive_closure does not copy attributes !
                mask = G.nodes[n]['mask']
                for succ in TC.successors (n):
                    G.nodes[succ]['ancestors'] |= mask

            # save the graph for later
            stemmas[pass_id - 1] = G

        # Matrix mss x passages containing the bitmask of the current reading
        mask_matrix     = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the parent readings
        parent_matrix   = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the ancestral readings
        ancestor_matrix = np.zeros ((val.n_mss, val.n_passages), np.uint64)

        # load ms x pass
        res = execute (conn, """
        SELECT pass_id - 1 AS pass_id,
               ms_id   - 1 AS ms_id,
               labez_clique (labez, clique) AS labez_clique
        FROM apparatus_cliques_view a
        WHERE labez !~ '^z[u-z]' AND cbgm
        ORDER BY pass_id
        """, parameters)

        LocStemEd = collections.namedtuple ('LocStemEd', 'pass_id ms_id labez_clique')
        rows = list (map (LocStemEd._make, res))

        # If ((current bitmask of ms j) and (ancestor bitmask of ms k) > 0) then
        # ms j is an ancestor of ms k.

        error_count = 0
        for row in rows:
            try:
                attrs = stemmas[row.pass_id].nodes[row.labez_clique]
                mask_matrix     [row.ms_id, row.pass_id] = attrs['mask']
                parent_matrix   [row.ms_id, row.pass_id] = attrs['parents']
                ancestor_matrix [row.ms_id, row.pass_id] = attrs['ancestors']
            except KeyError:
                error_count += 1
                # print (row.pass_id + 1)
                # print (str (e))

        # Matrix mss x passages containing True if source is unclear (s1 = '?')
        quest_matrix = np.bitwise_and (parent_matrix, 1)  # 1 means source unclear

        if error_count:
            log (logging.WARNING, "Could not find labez and clique in LocStem in %d cases." % error_count)
        log (logging.DEBUG, "mask:\n"      + str (mask_matrix))
        log (logging.DEBUG, "parents:\n"   + str (parent_matrix))
        log (logging.DEBUG, "ancestors:\n" + str (ancestor_matrix))
        log (logging.DEBUG, "quest:\n"     + str (quest_matrix))

        def postco (mask_matrix, anc_matrix):

            local_stemmas_with_loops = set ()

            # Matrix range x ms x ms with count of the passages that are older in ms1 than in ms2
            ancestor_matrix = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

            # Matrix range x ms x ms with count of the passages whose relationship is unclear in ms1 and ms2
            unclear_matrix  = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    # See: VGA/VGActs_allGenTab3Ph3.pl

                    # set bit if the reading of j is ancestral to the reading of k
                    varidj_is_older = np.bitwise_and (mask_matrix[j], anc_matrix[k]) > 0
                    varidk_is_older = np.bitwise_and (mask_matrix[k], anc_matrix[j]) > 0

                    if j == 0 and k > 0 and varidk_is_older.any ():
                        log (logging.ERROR, "Found varid older than A in msid: %d = %s"
                             % (k, np.nonzero (varidk_is_older)))

                    # error check for loops
                    if do_checks:
                        check = np.logical_and (varidj_is_older, varidk_is_older)
                        if np.any (check):
                            not_check       = np.logical_not (check)
                            varidj_is_older = np.logical_and (varidj_is_older, not_check)
                            varidk_is_older = np.logical_and (varidk_is_older, not_check)

                            local_stemmas_with_loops |= set (np.nonzero (check)[0])

                    # wenn die vergl. Hss. von einander abweichen u. eine von ihnen
                    # Q1 = '?' hat, UND KEINE VON IHNEN QUELLE DER ANDEREN IST, ist
                    # die Beziehung 'UNCLEAR'

                    unclear = np.logical_and (val.def_matrix[j], val.def_matrix[k])
                    unclear = np.logical_and (unclear, np.not_equal (val.labez_matrix[j], val.labez_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_or (quest_matrix[j], quest_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_not (np.logical_or (varidj_is_older, varidk_is_older)))

                    ancestor_matrix[:,j,k] = count_by_range (varidj_is_older, val.range_starts, val.range_ends)
                    unclear_matrix[:,j,k]  = count_by_range (unclear, val.range_starts, val.range_ends)

            if local_stemmas_with_loops:
                log (logging.ERROR, "Found loops in local stemmata: %s" % sorted (local_stemmas_with_loops))

            return ancestor_matrix, unclear_matrix

        val.parent_matrix,   val.unclear_parent_matrix   = postco (mask_matrix, parent_matrix)
        val.ancestor_matrix, val.unclear_ancestor_matrix = postco (mask_matrix, ancestor_matrix)


def write_affinity_table (dba, parameters, val):
    """Write back the new affinity (and ms_ranges) tables.

    """

    with dba.engine.begin () as conn:
        # perform sanity tests

        # varid older than ms A
        if val.ancestor_matrix[0,:,0].any ():
            log (logging.ERROR, "Found varid older than A in msids: %s"
                 % (np.nonzero (val.ancestor_matrix[0,:,0])))

        # norel < 0
        norel_matrix = (val.and_matrix - val.eq_matrix - val.ancestor_matrix -
                        np.transpose (val.ancestor_matrix, (0, 2, 1)) - val.unclear_ancestor_matrix)
        if np.less (norel_matrix, 0).any ():
            log (logging.ERROR, "norel < 0 in mss. %s"
                 % (np.nonzero (np.less (norel_matrix, 0))))

        # calculate ranges lengths using numpy
        params = []
        for i in range (0, val.n_mss):
            for range_ in val.ranges:
                length = int (np.sum (val.def_matrix[i, range_.start:range_.end]))
                params.append ( { 'ms_id': i + 1, 'range': range_.rg_id, 'length': length } )

        executemany (conn, """
        UPDATE ms_ranges
        SET length = :length
        WHERE ms_id = :ms_id AND rg_id = :range
        """, parameters, params)

        log (logging.INFO, "  Filling Affinity table ...")

        # execute (conn, "TRUNCATE affinity", parameters) # fast but needs access exclusive lock
        execute (conn, "DELETE FROM affinity", parameters)

        for i, range_ in enumerate (val.ranges):
            values = []
            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    if j != k:
                        common = int (val.and_matrix[i,j,k])
                        equal  = int (val.eq_matrix[i,j,k])
                        if common > 0:
                            values.append ( (
                                range_.rg_id,
                                j + 1,
                                k + 1,
                                float (equal) / common,
                                common,
                                equal,
                                int (val.ancestor_matrix[i,j,k]),
                                int (val.ancestor_matrix[i,k,j]),
                                int (val.unclear_ancestor_matrix[i,j,k]),
                                int (val.parent_matrix[i,j,k]),
                                int (val.parent_matrix[i,k,j]),
                                int (val.unclear_parent_matrix[i,j,k]),
                            ) )

            # speed gain for using executemany_raw: 65s to 55s :-(
            # probably the bottleneck here is string formatting with %s
            executemany_raw (conn, """
            INSERT INTO affinity (rg_id, ms_id1, ms_id2,
                                  affinity, common, equal,
                                  older, newer, unclear,
                                  p_older, p_newer, p_unclear)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, parameters, values)

        log (logging.DEBUG, "eq:"        + str (val.eq_matrix))
        log (logging.DEBUG, "ancestor:"  + str (val.ancestor_matrix))
        log (logging.DEBUG, "unclear:"   + str (val.unclear_ancestor_matrix))
        log (logging.DEBUG, "and:"       + str (val.and_matrix))
