
""" This module defines a series of exceptions used throughout this project """


class TournamentBaseError( Exception ):
    """ The base error class for the project """
    pass

class TriceBotAPIError( TournamentBaseError ):
    """ Errors for when an unhandled or unknown tricebot error occurs """
    pass

class DeckBaseError( TournamentBaseError ):
    """ The base error class for the deck module """
    pass

class DecklistError( DeckBaseError ):
    """ The error raised when the given decklist has an issue """
    pass

class CodFileError( DeckBaseError ):
    """ The error raised when there is an error in a cod file """
    pass

class DeckRetrievalError( DeckBaseError ):
    """ The error raised when a deck can not be retrieved from a URL """
    pass




