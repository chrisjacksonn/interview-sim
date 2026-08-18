# A mutant is one plausible break. Quote a unique snippet of reference.py
# verbatim as OLD and the broken version as NEW; the gate composes it against
# the reference and the hidden suite must kill it. Rename this file to name
# the break (files starting with _ are not counted). A full standalone
# solution file also works, for a break a substitution cannot express.
OLD = "return actual >= value"
NEW = "return actual > value"
