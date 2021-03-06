from statements import *
from pos_tagging import *
from agreement import *
from semantics import *

def sem(tr):
    """translates a syntax tree into a logical lambda expression (in string form)"""
    rule = top_level_rule(tr)
    if (tr.node == 'P'): # correctamundo
        return tr[0][0]
    elif tr.node == 'N': # correctamundo
        return '(\\x.' + tr[0][0] + '(x))'   # \\ is the escape sequence for \
    elif tr.node == 'A': # correctamundo
        return '(\\x.' + tr[0][0] + '(x))'
    elif tr.node == 'T': # correctamundo
        return '(\\y. \\x. ' + tr[0][0] + '(x,y))'
    elif tr.node == 'I': # correctamundo
        return '(\\x.' + tr[0][0] + '(x))'

    # S Expansions
    elif rule == 'S -> WHO QP QM': # correctamundo
        return sem(tr[1])
    elif rule == 'S -> WHICH Nom QP QM':
        return '(\\x.(' + sem(tr[1]) + '(x) & ' + sem(tr[2]) + '(x)))'

    # QP Expansions
    elif rule == 'QP -> VP': # correctamundo
        return sem(tr[0])
    elif rule == 'QP -> DO NP T':
        return '(\\x. exists y.(' + sem(tr[1]) + '(y) & ' + sem(tr[2]) + '(x)(y)))'

    # VP Expansions
    elif rule == 'VP -> T NP': # correctamundo
        return '(\\x. exists y.(' + sem(tr[1]) + '(y) & ' + sem(tr[0]) + '(y)(x)))'
    elif rule == 'VP -> BE NP' or rule == 'VP -> BE A':
        return '(\\x.' + sem(tr[1]) + '(x))'
    elif rule == 'VP -> VP AND VP':
        return '(\\x.' + sem(tr[0]) + '(x) & ' + sem(tr[1]) + '(x)))'
    elif rule == 'VP -> I':
        return '(\\x' + sem(tr[0]) + '(x))'

    # NP Expansions
    elif rule == 'NP -> P':
        return '(\\x.x=' + sem(tr[0]) + ')'
    elif rule == 'NP -> AR Nom':
        return sem(tr[1])
    elif rule == 'NP -> Nom':
        return sem(tr[0])

    # Nom Expansions
    elif rule == 'Nom -> AN':
        return sem(tr[0])
    elif rule == 'Nom -> AN Rel':
        return '(\\x.(' + sem(tr[0]) + '(x) & ' + sem(tr[1]) + '(x)))'

    # AN Expansions
    elif (rule == 'AN -> A AN'):
        return '(\\x.(' + sem(tr[0]) + '(x) & ' + sem(tr[1]) + '(x)))'
    elif (rule == 'AN -> N'):
        return sem(tr[0])

    # Rel Expansions
    elif rule == 'Rel -> WHO VP':
        return '(\\x.' + sem(tr[1]) + '(x))'
    

# Logic parser for lambda expressions

from nltk import LogicParser
lp = LogicParser()

# Lambda expressions can now be checked and simplified as follows:

#   A = lp.parse('(\\x.((\\P.P(x,x))(loves)))(John)')
#   B = lp.parse(sem(tr))  # for some tree tr
#   A.simplify()
#   B.simplify()


# Model checker

from nltk.sem.logic import *

# Can use: A.variable, A.term, A.term.first, A.term.second, A.function, A.args

def interpret_const_or_var(s,bindings,entities):
    if (s in entities): # s a constant
        return s
    else:               # s a variable
        return [p[1] for p in bindings if p[0]==s][0]  # finds most recent binding

def model_check (P,bindings,entities,fb):
    if (isinstance (P,ApplicationExpression)):
        if (len(P.args)==1):
            pred = str(P.function)
            arg = interpret_const_or_var(str(P.args[0]),bindings,entities)
            return fb.queryUnary(pred,arg)
        else:
            pred = str(P.function.function)
            arg0 = interpret_const_or_var(str(P.args[0]),bindings,entities)
            arg1 = interpret_const_or_var(str(P.args[1]),bindings,entities)
            return fb.queryBinary(pred,arg0,arg1)
    elif (isinstance (P,EqualityExpression)):
        arg0 = interpret_const_or_var(str(P.first),bindings,entities)
        arg1 = interpret_const_or_var(str(P.second),bindings,entities)
        return (arg0 == arg1)
    elif (isinstance (P,AndExpression)):
        return (model_check (P.first,bindings,entities,fb) and
                model_check (P.second,bindings,entities,fb))
    elif (isinstance (P,ExistsExpression)):
        v = str(P.variable)
        P1 = P.term
        for e in entities:
            bindings1 = [(v,e)] + bindings
            if (model_check (P1,bindings1,entities,fb)):
                return True
        return False

def find_all_solutions (L,entities,fb):
    v = str(L.variable)
    P = L.term
    return [e for e in entities if model_check(P,[(v,e)],entities,fb)]


# Interactive dialogue session

def fetch_input():
    s = raw_input('$$ ')
    while (s.split() == []):
        s = raw_input('$$ ')
    return s    

def output(s):
    print ('     '+s)

def dialogue():
    lx = Lexicon()
    fb = FactBase()
    output('')
    s = fetch_input()
    while (s.split() == []):
        s = raw_input('$$ ')
    while (s != 'exit'):
        if (s[-1]=='?'):
            sent = s[:-1] + ' ?'  # tolerate absence of space before '?'
            wds = sent.split()
            trees = all_valid_parses(wds,lx)
            if (len(trees)==0):
                output ("Eh??")
            elif (len(trees)>1):
                output ("Ambiguous!")
            else:
                tr = restore_words (trees[0],wds)
                lam_exp = lp.parse(sem(tr))
                print lam_exp
                L = lam_exp.simplify()
                print L  # useful for debugging
                print ''
                entities = lx.getAll('P')
                results = find_all_solutions (L,entities,fb)
                if (results == []):
                    if (wds[0].lower() == 'who'):
                        output ("No one")
                    else:
                        output ("None")
                else:
                    buf = ''
                    for r in results:
                        buf = buf + r + '  '
                    output (buf)
        else:
            if (s[-1]=='.'):
                s = s[:-1]  # tolerate final full stop
            wds = s.split()
            msg = process_statement(wds,lx,fb)
            if (msg == ''):
                output ("OK.")
            else:
                output ("Sorry - " + msg)
        s = fetch_input()
