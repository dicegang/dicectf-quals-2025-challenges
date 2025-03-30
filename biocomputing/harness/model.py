from typing import List
from dataclasses import dataclass
from collections import namedtuple


# Reaction types
ADD = namedtuple('ADD', ['terms'])
DIV = namedtuple('DIV', ['a', 'b'])
MUL = namedtuple('MUL', ['terms'])
SUB = namedtuple('SUB', ['a', 'b'])
POW = namedtuple('POW', ['a', 'b'])
MAX = namedtuple('MAX', ['terms'])
MIN = namedtuple('MIN', ['terms'])

# Leaf types
CONST = namedtuple('CONST', ['value'])
VAR = namedtuple('VAR', ['name'])

RATE_TYPE = ADD | DIV | MUL | POW | SUB | MAX | MIN | CONST | VAR


@dataclass
class Species:
    name: str
    initial_amount: float

@dataclass
class SpeciesReference:
    name: str

@dataclass
class Reaction:
    name: str
    reactants: List[SpeciesReference]
    products: List[SpeciesReference]
    rate: RATE_TYPE

@dataclass
class Parameter:
    name: str
    value: float

@dataclass
class Model:
    parameters: List[Parameter]
    species: List[Species]
    reactions: List[Reaction]



class XMLWriter:
    def __init__(self, model: Model):
        self.model = model
        self.parts = []

    def write_parameters(self):
        self.parts.append('<listOfParameters>')
        for parameter in self.model.parameters:
            self.parts.append(f'<parameter id="{parameter.name}" value="{parameter.value}" constant="true"/>')
        self.parts.append('</listOfParameters>')

    def write_compartments(self):
        self.parts.append('<listOfCompartments>')
        self.parts.append('<compartment id="cell" size="1"/>')
        self.parts.append('</listOfCompartments>')

    def write_species(self):
        self.parts.append('<listOfSpecies>')
        for species in self.model.species:
            self.parts.append(f'<species id="{species.name}" compartment="cell" initialAmount="{species.initial_amount}"/>')
        self.parts.append('</listOfSpecies>')

    def write_reactions(self):
        self.parts.append("<listOfReactions>")
        for reaction in self.model.reactions:
            self.parts.append(f'<reaction id="{reaction.name}">')
            self.parts.append('<listOfReactants>')
            for reactant in reaction.reactants:
                self.parts.append(f'<speciesReference species="{reactant.name}"/>')
            self.parts.append('</listOfReactants>')
            self.parts.append('<listOfProducts>')
            for product in reaction.products:
                self.parts.append(f'<speciesReference species="{product.name}"/>')
            self.parts.append('</listOfProducts>')
            self.write_kinetic_law(reaction.rate)
            self.parts.append('</reaction>')
        self.parts.append('</listOfReactions>')

    def write_kinetic_law(self, rate: RATE_TYPE):
        self.parts.append('<kineticLaw>')
        self.parts.append('<math xmlns="http://www.w3.org/1998/Math/MathML">')
        self.write_rate(rate)
        self.parts.append('</math>')
        self.parts.append('</kineticLaw>')

    def write_rate(self, rate: RATE_TYPE):
        match rate:
            case ADD(terms):
                self.parts.append('<apply><plus/>')
                for term in terms:
                    self.write_rate(term)
                self.parts.append('</apply>')
            case SUB(a, b):
                self.parts.append('<apply><minus/>')
                self.write_rate(a)
                self.write_rate(b)
                self.parts.append('</apply>')
            case DIV(a, b):
                self.parts.append('<apply><divide/>')
                self.write_rate(a)
                self.write_rate(b)
                self.parts.append('</apply>')
            case MAX(terms):
                self.parts.append('<apply><max/>')
                for term in terms:
                    self.write_rate(term)
                self.parts.append('</apply>')
            case MIN(terms):
                self.parts.append('<apply><min/>')
                for term in terms:
                    self.write_rate(term)
                self.parts.append('</apply>')
            case MUL(terms):
                self.parts.append('<apply><times/>')
                for term in terms:
                    self.write_rate(term)
                self.parts.append('</apply>')
            case POW(a, b):
                self.parts.append('<apply><power/>')
                self.write_rate(a)
                self.write_rate(b)
                self.parts.append('</apply>')
            case CONST(value):
                self.parts.append(f'<cn>{value}</cn>')
            case VAR(name):
                self.parts.append(f'<ci>{name}</ci>')

    def write(self):
        self.parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        self.parts.append('<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">')
        self.parts.append('<model id="circuit">')

        self.write_parameters()
        self.write_compartments()
        self.write_species()
        self.write_reactions()

        self.parts.append('</model>')
        self.parts.append('</sbml>')
        return ''.join(self.parts)
