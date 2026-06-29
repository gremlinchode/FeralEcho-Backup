"""
Library Knowledge Base
----------------------
This file maintains a dynamic record of Python libraries that Echo can access.

Purpose:
    - Teach Echo what each library does and how it might be used.
    - Automatically detect and register new libraries when installed.
    - Provide a readable description for self-documentation and reflection.

Behavior:
    - On import, it checks installed libraries via importlib.metadata.
    - If a library is missing from LIBRARY_KNOWLEDGE, it generates
      a simple summary using metadata or Ollama and updates this file automatically.
    - Echo can query this file for explanations or possible use cases.

Last auto-update: dynamically generated each run.
"""

import os
import datetime
import importlib.metadata
import textwrap
import pprint
import subprocess

# --- Initialize library knowledge ---
LIBRARY_KNOWLEDGE = {   'absl-py': {   'category': 'Networking',
                   'purpose': 'Abseil Python Common Libraries, see '
                              'https://github.com/abseil/abseil-py.',
                   'use_cases': ['Potentially used for networking tasks.']},
    'accelerate': {   'category': 'Machine Learning',
                      'purpose': 'Accelerate',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'aiofiles': {   'category': 'Networking',
                    'purpose': 'File support for asyncio.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'aiohappyeyeballs': {   'category': 'Networking',
                            'purpose': 'Happy Eyeballs for asyncio',
                            'use_cases': [   'Potentially used for networking '
                                             'tasks.']},
    'aiohttp': {   'category': 'Networking',
                   'purpose': 'Async http client/server framework (asyncio)',
                   'use_cases': ['Potentially used for networking tasks.']},
    'aiosignal': {   'category': 'Machine Learning',
                     'purpose': 'aiosignal: a list of registered asynchronous '
                                'callbacks',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'aiosqlite': {   'category': 'Database / Storage',
                     'purpose': 'asyncio bridge to the standard sqlite3 module',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'alembic': {   'category': 'Data Analysis',
                   'purpose': 'A database migration tool for SQLAlchemy.',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'annotated-types': {   'category': 'Machine Learning',
                           'purpose': 'Reusable constraint types to use with '
                                      'typing.Annotated',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'anthropic': {   'category': 'Web Framework',
                     'purpose': 'The official Python library for the anthropic '
                                'API',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'antlr4-python3-runtime': {   'category': 'Unknown / General',
                                  'purpose': 'ANTLR 4.9.3 runtime for Python '
                                             '3.7',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'anyio': {   'category': 'Networking',
                 'purpose': 'High-level concurrency and networking framework '
                            'on top of asyncio or Trio',
                 'use_cases': ['Potentially used for networking tasks.']},
    'appdirs': {   'category': 'Data Analysis',
                   'purpose': 'A small Python module for determining '
                              'appropriate platform-specific dirs, e.g. a '
                              '"user data dir".',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'appnope': {   'category': 'Unknown / General',
                   'purpose': 'Disable App Nap on macOS >= 10.9',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'apricot-select': {   'category': 'Unknown / General',
                          'purpose': 'apricot is a package for submodular '
                                     'selection of representative sets for '
                                     'machine learning models.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'apscheduler': {   'category': 'Unknown / General',
                       'purpose': 'In-process task scheduler with Cron-like '
                                  'capabilities',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'arabic-reshaper': {   'category': 'Web Framework',
                           'purpose': 'Reconstruct Arabic sentences to be used '
                                      'in applications that do not support '
                                      'Arabic',
                           'use_cases': [   'Potentially used for web '
                                            'framework tasks.']},
    'archspec': {   'category': 'Unknown / General',
                    'purpose': 'A library to query system architecture',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'argon2-cffi': {   'category': 'Security / Encryption',
                       'purpose': 'Argon2 for Python',
                       'use_cases': [   'Potentially used for security / '
                                        'encryption tasks.']},
    'argon2-cffi-bindings': {   'category': 'Security / Encryption',
                                'purpose': 'Low-level CFFI bindings for Argon2',
                                'use_cases': [   'Potentially used for '
                                                 'security / encryption '
                                                 'tasks.']},
    'arrow': {   'category': 'Unknown / General',
                 'purpose': 'Better dates & times for Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'arviz': {   'category': 'Unknown / General',
                 'purpose': 'Exploratory analysis of Bayesian models',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'astor': {   'category': 'Unknown / General',
                 'purpose': 'Read/rewrite/write Python ASTs',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'asttokens': {   'category': 'Unknown / General',
                     'purpose': 'Annotate AST trees with source code positions',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'astunparse': {   'category': 'Unknown / General',
                      'purpose': 'An AST unparser for Python',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'async-lru': {   'category': 'Networking',
                     'purpose': 'Simple LRU cache for asyncio',
                     'use_cases': ['Potentially used for networking tasks.']},
    'asyncer': {   'category': 'Machine Learning',
                   'purpose': 'Asyncer, async and await, focused on developer '
                              'experience.',
                   'use_cases': [   'Potentially used for machine learning '
                                    'tasks.']},
    'attrs': {   'category': 'Unknown / General',
                 'purpose': 'Classes Without Boilerplate',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'audioread': {   'category': 'Database / Storage',
                     'purpose': 'Multi-library, cross-platform audio decoding.',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'auth0-python': {   'category': 'Security / Encryption',
                        'purpose': 'Auto-discovered Python library named '
                                   "'auth0-python'. Purpose not yet "
                                   'documented.',
                        'use_cases': [   'Potentially used for security / '
                                         'encryption tasks.']},
    'autogen-agentchat': {   'category': 'Unknown / General',
                             'purpose': 'AutoGen agents and teams library',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'autogen-core': {   'category': 'Unknown / General',
                        'purpose': 'Foundational interfaces and agent runtime '
                                   'implementation for AutoGen',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'avalanche-lib': {   'category': 'Unknown / General',
                         'purpose': 'Avalanche: a Comprehensive Framework for '
                                    'Continual Learning Research',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'babel': {   'category': 'Unknown / General',
                 'purpose': 'Internationalization utilities',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'backcall': {   'category': 'Web Framework',
                    'purpose': 'Specifications for callback functions passed '
                               'in to an API',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'backoff': {   'category': 'Unknown / General',
                   'purpose': 'Function decoration for backoff and retry',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'bambi': {   'category': 'Unknown / General',
                 'purpose': 'BAyesian Model Building Interface in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'banks': {   'category': 'Unknown / General',
                 'purpose': 'A prompt programming language',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'baron': {   'category': 'Unknown / General',
                 'purpose': 'Full Syntax Tree for python to make writing '
                            'refactoring code a realist task',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'bcrypt': {   'category': 'Unknown / General',
                  'purpose': 'Modern password hashing for your software and '
                             'your servers',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'beartype': {   'category': 'Unknown / General',
                    'purpose': 'Unbearably fast near-real-time hybrid '
                               'runtime-static type-checking in pure Python.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'beautifulsoup4': {   'category': 'Machine Learning',
                          'purpose': 'Screen-scraping library',
                          'use_cases': [   'Potentially used for machine '
                                           'learning tasks.']},
    'bible': {   'category': 'Machine Learning',
                 'purpose': 'Bible reference classes',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'bidict': {   'category': 'Unknown / General',
                  'purpose': 'The bidirectional mapping library for Python.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'bleach': {   'category': 'Machine Learning',
                  'purpose': 'An easy safelist-based HTML-sanitizing tool.',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'blessed': {   'category': 'Database / Storage',
                   'purpose': 'Easy, practical library for making terminal '
                              'apps, by providing an elegant, well-documented '
                              'interface to Colors, Keyboard input, and screen '
                              'Positioning capabilities.',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'blinker': {   'category': 'Unknown / General',
                   'purpose': 'Fast, simple object-to-object and broadcast '
                              'signaling',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'blis': {   'category': 'Machine Learning',
                'purpose': 'The Blis BLAS-like linear algebra library, as a '
                           'self-contained C-extension.',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'blosc2': {   'category': 'Unknown / General',
                  'purpose': 'A fast & compressed ndarray library with a '
                             'flexible compute engine.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'bokeh': {   'category': 'Visualization',
                 'purpose': 'Interactive plots and applications in the browser '
                            'from Python',
                 'use_cases': ['Potentially used for visualization tasks.']},
    'boltons': {   'category': 'Unknown / General',
                   'purpose': "When they're not builtins, they're boltons.",
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'brian2': {   'category': 'Machine Learning',
                  'purpose': 'A clock-driven simulator for spiking neural '
                             'networks',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'brotli': {   'category': 'Unknown / General',
                  'purpose': 'Python bindings for the Brotli compression '
                             'library',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'build': {   'category': 'Unknown / General',
                 'purpose': 'A simple, correct Python build frontend',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'cachetools': {   'category': 'Unknown / General',
                      'purpose': 'Extensible memoizing collections and '
                                 'decorators',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'catalogue': {   'category': 'Unknown / General',
                     'purpose': 'Super lightweight function registries for '
                                'your library',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'cattrs': {   'category': 'Data Analysis',
                  'purpose': 'Composable complex class support for attrs and '
                             'dataclasses.',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'certifi': {   'category': 'Unknown / General',
                   'purpose': "Python package for providing Mozilla's CA "
                              'Bundle.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'cffi': {   'category': 'Unknown / General',
                'purpose': 'Foreign Function Interface for Python calling C '
                           'code.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'cfgv': {   'category': 'Unknown / General',
                'purpose': 'Validate configuration and produce human readable '
                           'error messages.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'charset-normalizer': {   'category': 'Machine Learning',
                              'purpose': 'The Real First Universal Charset '
                                         'Detector. Open, modern and actively '
                                         'maintained alternative to Chardet.',
                              'use_cases': [   'Potentially used for machine '
                                               'learning tasks.']},
    'chromadb': {   'category': 'Unknown / General',
                    'purpose': 'Chroma.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'clarabel': {   'category': 'Unknown / General',
                    'purpose': 'Clarabel Conic Interior Point Solver for Rust '
                               '/ Python',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'click': {   'category': 'Unknown / General',
                 'purpose': 'Composable command line interface toolkit',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'cloudpathlib': {   'category': 'Unknown / General',
                        'purpose': 'pathlib-style classes for cloud storage '
                                   'services.',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'cloudpickle': {   'category': 'Unknown / General',
                       'purpose': 'Pickler class to extend the standard '
                                  'pickle.Pickler functionality',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'cmeel': {   'category': 'Unknown / General',
                 'purpose': 'Create Wheel from CMake projects',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'colorama': {   'category': 'Database / Storage',
                    'purpose': 'Cross-platform colored terminal text.',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'coloredlogs': {   'category': 'Unknown / General',
                       'purpose': "Colored terminal output for Python's "
                                  'logging module',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'colorlog': {   'category': 'Unknown / General',
                    'purpose': "Add colours to the output of Python's logging "
                               'module.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'comm': {   'category': 'Unknown / General',
                'purpose': 'Jupyter Python Comm implementation, for usage in '
                           'ipykernel, xeus-python etc.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'commonmark': {   'category': 'Unknown / General',
                      'purpose': 'Python parser for the CommonMark Markdown '
                                 'spec',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'confection': {   'category': 'Unknown / General',
                      'purpose': 'The sweetest config system for Python',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'cons': {   'category': 'Unknown / General',
                'purpose': 'An implementation of Lisp/Scheme-like cons in '
                           'Python.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'contourpy': {   'category': 'Unknown / General',
                     'purpose': 'Python library for calculating contours of 2D '
                                'quadrilateral grids',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'crewai': {   'category': 'Machine Learning',
                  'purpose': 'Cutting-edge framework for orchestrating '
                             'role-playing, autonomous AI agents. By fostering '
                             'collaborative intelligence, CrewAI empowers '
                             'agents to work together seamlessly, tackling '
                             'complex tasks.',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'cryptography': {   'category': 'Visualization',
                        'purpose': 'cryptography is a package which provides '
                                   'cryptographic recipes and primitives to '
                                   'Python developers.',
                        'use_cases': [   'Potentially used for visualization '
                                         'tasks.']},
    'cvxopt': {   'category': 'Unknown / General',
                  'purpose': 'Convex optimization package',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'cycler': {   'category': 'Unknown / General',
                  'purpose': 'Composable style cycles',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'cymem': {   'category': 'Unknown / General',
                 'purpose': 'Manage calls to calloc/free through Cython',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'cython': {   'category': 'Unknown / General',
                  'purpose': 'The Cython compiler for writing C extensions in '
                             'the Python language.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'daqp': {   'category': 'Unknown / General',
                'purpose': 'DAQP: A dual active-set QP solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'dataclasses-json': {   'category': 'Data Analysis',
                            'purpose': 'Easily serialize dataclasses to and '
                                       'from JSON.',
                            'use_cases': [   'Potentially used for data '
                                             'analysis tasks.']},
    'datasets': {   'category': 'Data Analysis',
                    'purpose': 'HuggingFace community-driven open-source '
                               'library of datasets',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'debugpy': {   'category': 'Unknown / General',
                   'purpose': 'An implementation of the Debug Adapter Protocol '
                              'for Python',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'decorator': {   'category': 'Unknown / General',
                     'purpose': 'Decorators for Humans',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'defusedxml': {   'category': 'Machine Learning',
                      'purpose': 'XML bomb protection for Python stdlib '
                                 'modules',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'deprecated': {   'category': 'Unknown / General',
                      'purpose': 'Python @deprecated decorator to deprecate '
                                 'old python classes, functions or methods.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'dill': {   'category': 'Unknown / General',
                'purpose': 'serialize all of Python',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'dirtyjson': {   'category': 'Data Analysis',
                     'purpose': 'JSON decoder for Python that can extract data '
                                'from the muck',
                     'use_cases': [   'Potentially used for data analysis '
                                      'tasks.']},
    'diskcache': {   'category': 'Unknown / General',
                     'purpose': 'Disk Cache -- Disk and file backed persistent '
                                'cache.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'distlib': {   'category': 'Unknown / General',
                   'purpose': 'Distribution utilities',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'distro': {   'category': 'Web Framework',
                  'purpose': 'Distro - an OS platform information API',
                  'use_cases': ['Potentially used for web framework tasks.']},
    'dnd-5e-core': {   'category': 'Machine Learning',
                       'purpose': 'Complete D&D 5e Rules Engine: 24 Class '
                                  'Abilities, 20 Racial Traits, 40+ '
                                  'Subclasses, Multiclassing, Advanced Combat, '
                                  '332 Monsters, 319+ Spells, 49 Magic Items, '
                                  'Treasure System, Conditions. 100% Offline '
                                  'with 8.7MB bundled data.',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'dnd-character': {   'category': 'Unknown / General',
                         'purpose': 'make Dungeons & Dragons characters as '
                                    'serializable objects',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'dndice': {   'category': 'Unknown / General',
                  'purpose': 'An engine to parse and evaluate D&D-inspired '
                             'roll expressions',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'dnspython': {   'category': 'Unknown / General',
                     'purpose': 'DNS toolkit',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'docstring_parser': {   'category': 'Database / Storage',
                            'purpose': 'Parse Python docstrings in reST, '
                                       'Google and Numpydoc format',
                            'use_cases': [   'Potentially used for database / '
                                             'storage tasks.']},
    'dspy': {   'category': 'Unknown / General',
                'purpose': 'DSPy',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'durationpy': {   'category': 'Unknown / General',
                      'purpose': 'Module for converting between '
                                 "datetime.timedelta and Go's Duration "
                                 'strings.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ecos': {   'category': 'Database / Storage',
                'purpose': 'This is the Python package for ECOS: Embedded Cone '
                           'Solver. See Github page for more information.',
                'use_cases': [   'Potentially used for database / storage '
                                 'tasks.']},
    'editor': {   'category': 'Unknown / General',
                  'purpose': '🖋 Open the default text editor 🖋',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'elementpath': {   'category': 'Machine Learning',
                       'purpose': 'XPath 1.0/2.0/3.0/3.1 parsers and selectors '
                                  'for ElementTree and lxml',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'en_core_web_sm': {   'category': 'Unknown / General',
                          'purpose': 'English pipeline optimized for CPU. '
                                     'Components: tok2vec, tagger, parser, '
                                     'senter, ner, attribute_ruler, '
                                     'lemmatizer.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'esprima': {   'category': 'Unknown / General',
                   'purpose': 'ECMAScript parsing infrastructure for '
                              'multipurpose analysis in Python',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'et_xmlfile': {   'category': 'Machine Learning',
                      'purpose': 'An implementation of lxml.xmlfile for the '
                                 'standard library',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'etuples': {   'category': 'Unknown / General',
                   'purpose': 'Python S-expression emulation using tuple-like '
                              'objects.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'executing': {   'category': 'Database / Storage',
                     'purpose': 'Get the currently executing AST node of a '
                                'frame, and other information',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'expyriment': {   'category': 'Unknown / General',
                      'purpose': 'A Python library for cognitive and '
                                 'neuroscientific experiments',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'face': {   'category': 'Unknown / General',
                'purpose': 'A command-line application framework (and CLI '
                           'parser). Friendly for users, full-featured for '
                           'developers.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'faiss-cpu': {   'category': 'Machine Learning',
                     'purpose': 'A library for efficient similarity search and '
                                'clustering of dense vectors.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'fastapi': {   'category': 'Web Framework',
                   'purpose': 'FastAPI framework, high performance, easy to '
                              'learn, fast to code, ready for production',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'fastjsonschema': {   'category': 'Unknown / General',
                          'purpose': 'Fastest Python implementation of JSON '
                                     'schema',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'fastkde': {   'category': 'Unknown / General',
                   'purpose': 'Tools for fast and robust univariate and '
                              'multivariate kernel density estimation',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'fastuuid': {   'category': 'Unknown / General',
                    'purpose': "Python bindings to Rust's UUID library.",
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'feedparser': {   'category': 'Unknown / General',
                      'purpose': 'Universal feed parser, handles RSS 0.9x, RSS '
                                 '1.0, RSS 2.0, CDF, Atom 0.3, and Atom 1.0 '
                                 'feeds',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ffmpy': {   'category': 'Unknown / General',
                 'purpose': 'A simple Python wrapper for FFmpeg',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'ffpyplayer': {   'category': 'Unknown / General',
                      'purpose': 'A cython implementation of an ffmpeg based '
                                 'player.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'filelock': {   'category': 'Database / Storage',
                    'purpose': 'A platform independent file lock.',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'filetype': {   'category': 'Unknown / General',
                    'purpose': 'Infer file type and MIME type of any '
                               'file/buffer. No external dependencies.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'flask': {   'category': 'Web Framework',
                 'purpose': 'A simple framework for building complex web '
                            'applications.',
                 'use_cases': ['Potentially used for web framework tasks.']},
    'flask-socketio': {   'category': 'Web Framework',
                          'purpose': 'Socket.IO integration for Flask '
                                     'applications',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'flatbuffers': {   'category': 'Database / Storage',
                       'purpose': 'The FlatBuffers serialization format for '
                                  'Python',
                       'use_cases': [   'Potentially used for database / '
                                        'storage tasks.']},
    'flexcache': {   'category': 'Database / Storage',
                     'purpose': 'Saves and loads to the cache a transformed '
                                'versions of a source object.',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'flexparser': {   'category': 'Unknown / General',
                      'purpose': 'Parsing made fun ... using typing.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'fonttools': {   'category': 'Unknown / General',
                     'purpose': 'Tools to manipulate font files',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'formulae': {   'category': 'Database / Storage',
                    'purpose': 'Formulas for mixed-effects models in Python',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'fqdn': {   'category': 'Machine Learning',
                'purpose': 'Validates fully-qualified domain names against RFC '
                           '1123, so that they are acceptable to modern '
                           'bowsers',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'freetype-py': {   'category': 'Unknown / General',
                       'purpose': 'Freetype python bindings',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'frozendict': {   'category': 'Unknown / General',
                      'purpose': 'A simple immutable dictionary',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'frozenlist': {   'category': 'Unknown / General',
                      'purpose': 'A list-like structure which implements '
                                 'collections.abc.MutableSequence',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'fsspec': {   'category': 'Unknown / General',
                  'purpose': 'File-system specification',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'future': {   'category': 'Unknown / General',
                  'purpose': 'Clean single-source support for Python 3 and 2',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'gdown': {   'category': 'Unknown / General',
                 'purpose': 'Google Drive Public File/Folder Downloader',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'gepa': {   'category': 'Machine Learning',
                'purpose': 'A framework for optimizing textual system '
                           'components (AI prompts, code snippets, etc.) using '
                           'LLM-based reflection and Pareto-efficient '
                           'evolutionary search.',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'gevent': {   'category': 'Networking',
                  'purpose': 'Coroutine-based network library',
                  'use_cases': ['Potentially used for networking tasks.']},
    'git-python': {   'category': 'Unknown / General',
                      'purpose': 'combination and simplification of some '
                                 'useful git commands',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'gitdb': {   'category': 'Data Analysis',
                 'purpose': 'Git Object Database',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'gitpython': {   'category': 'Unknown / General',
                     'purpose': 'GitPython is a Python library used to '
                                'interact with Git repositories',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'glom': {   'category': 'Data Analysis',
                'purpose': 'A declarative object transformer and formatter, '
                           'for conglomerating nested data.',
                'use_cases': ['Potentially used for data analysis tasks.']},
    'gmpy2': {   'category': 'Unknown / General',
                 'purpose': 'gmpy2 interface to GMP, MPFR, and MPC for Python '
                            '3.7+',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'google-ai-generativelanguage': {   'category': 'Machine Learning',
                                        'purpose': 'Google Ai '
                                                   'Generativelanguage API '
                                                   'client library',
                                        'use_cases': [   'Potentially used for '
                                                         'machine learning '
                                                         'tasks.']},
    'google-api-core': {   'category': 'Web Framework',
                           'purpose': 'Google API client core library',
                           'use_cases': [   'Potentially used for web '
                                            'framework tasks.']},
    'google-api-python-client': {   'category': 'Web Framework',
                                    'purpose': 'Google API Client Library for '
                                               'Python',
                                    'use_cases': [   'Potentially used for web '
                                                     'framework tasks.']},
    'google-auth': {   'category': 'Security / Encryption',
                       'purpose': 'Google Authentication Library',
                       'use_cases': [   'Potentially used for security / '
                                        'encryption tasks.']},
    'google-auth-httplib2': {   'category': 'Networking',
                                'purpose': 'Google Authentication Library: '
                                           'httplib2 transport',
                                'use_cases': [   'Potentially used for '
                                                 'networking tasks.']},
    'google-generativeai': {   'category': 'Machine Learning',
                               'purpose': 'Google Generative AI High level API '
                                          'client library and tools.',
                               'use_cases': [   'Potentially used for machine '
                                                'learning tasks.']},
    'googleapis-common-protos': {   'category': 'Web Framework',
                                    'purpose': 'Common protobufs used in '
                                               'Google APIs',
                                    'use_cases': [   'Potentially used for web '
                                                     'framework tasks.']},
    'gputil': {   'category': 'Machine Learning',
                  'purpose': 'GPUtil is a Python module for getting the GPU '
                             'status from NVIDA GPUs using nvidia-smi.',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'gradio': {   'category': 'Machine Learning',
                  'purpose': 'Python library for easily interacting with '
                             'trained machine learning models',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'gradio_client': {   'category': 'Machine Learning',
                         'purpose': 'Python library for easily interacting '
                                    'with trained machine learning models',
                         'use_cases': [   'Potentially used for machine '
                                          'learning tasks.']},
    'graph-scheduler': {   'category': 'Visualization',
                           'purpose': 'A graph-based scheduler of nodes based '
                                      'on structure and conditions',
                           'use_cases': [   'Potentially used for '
                                            'visualization tasks.']},
    'graphviz': {   'category': 'Visualization',
                    'purpose': 'Simple Python interface for Graphviz',
                    'use_cases': ['Potentially used for visualization tasks.']},
    'greenlet': {   'category': 'Unknown / General',
                    'purpose': 'Lightweight in-process concurrent programming',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'griffe': {   'category': 'Web Framework',
                  'purpose': 'Signatures for entire Python programs. Extract '
                             'the structure, the frame, the skeleton of your '
                             'project, to generate API documentation or find '
                             'breaking changes in your API.',
                  'use_cases': ['Potentially used for web framework tasks.']},
    'groovy': {   'category': 'Unknown / General',
                  'purpose': 'A small Python library created to help '
                             'developers protect their applications from '
                             'Server Side Request Forgery (SSRF) attacks.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'grpcio': {   'category': 'Networking',
                  'purpose': 'HTTP/2-based RPC framework',
                  'use_cases': ['Potentially used for networking tasks.']},
    'grpcio-status': {   'category': 'Unknown / General',
                         'purpose': 'Status proto mapping for gRPC',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'gunicorn': {   'category': 'Networking',
                    'purpose': 'WSGI HTTP Server for UNIX',
                    'use_cases': ['Potentially used for networking tasks.']},
    'h11': {   'category': 'Networking',
               'purpose': 'A pure-Python, bring-your-own-I/O implementation of '
                          'HTTP/1.1',
               'use_cases': ['Potentially used for networking tasks.']},
    'h2': {   'category': 'Networking',
              'purpose': 'Pure-Python HTTP/2 protocol implementation',
              'use_cases': ['Potentially used for networking tasks.']},
    'h5netcdf': {   'category': 'Unknown / General',
                    'purpose': 'netCDF4 via h5py',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'h5py': {   'category': 'Unknown / General',
                'purpose': 'Read and write HDF5 files from Python',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'hf-xet': {   'category': 'Unknown / General',
                  'purpose': 'Fast transfer of large files with the Hugging '
                             'Face Hub.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'highspy': {   'category': 'Unknown / General',
                   'purpose': 'A thin set of pybind11 wrappers to HiGHS',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'hmmlearn': {   'category': 'Web Framework',
                    'purpose': 'Hidden Markov Models in Python with '
                               'scikit-learn like API',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'hpack': {   'category': 'Unknown / General',
                 'purpose': 'Pure-Python HPACK header encoding',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'html2image': {   'category': 'Machine Learning',
                      'purpose': 'Package acting as a wrapper around the '
                                 'headless mode of existing web browsers to '
                                 'generate images from URLs and from HTML+CSS '
                                 'strings or files.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'html2text': {   'category': 'Machine Learning',
                     'purpose': 'Turn HTML into equivalent Markdown-structured '
                                'text.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'httpcore': {   'category': 'Networking',
                    'purpose': 'A minimal low-level HTTP client.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'httplib2': {   'category': 'Networking',
                    'purpose': 'A comprehensive HTTP client library.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'httptools': {   'category': 'Networking',
                     'purpose': 'A collection of framework independent HTTP '
                                'protocol utils.',
                     'use_cases': ['Potentially used for networking tasks.']},
    'httpx': {   'category': 'Networking',
                 'purpose': 'The next generation HTTP client.',
                 'use_cases': ['Potentially used for networking tasks.']},
    'huggingface-hub': {   'category': 'Machine Learning',
                           'purpose': 'Client library to download and publish '
                                      'models, datasets and other repos on the '
                                      'huggingface.co hub',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'humanfriendly': {   'category': 'Unknown / General',
                         'purpose': 'Human friendly output for text interfaces '
                                    'using Python',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'hyperframe': {   'category': 'Networking',
                      'purpose': 'Pure-Python HTTP/2 framing',
                      'use_cases': ['Potentially used for networking tasks.']},
    'identify': {   'category': 'Unknown / General',
                    'purpose': 'File identification library for Python',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'idna': {   'category': 'Machine Learning',
                'purpose': 'Internationalized Domain Names in Applications '
                           '(IDNA)',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'ifaddr': {   'category': 'Database / Storage',
                  'purpose': 'Cross-platform network interface and IP address '
                             'enumeration library',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'imageio': {   'category': 'Data Analysis',
                   'purpose': 'Read and write images and video across all '
                              'major formats. Supports scientific and '
                              'volumetric data.',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'imageio-ffmpeg': {   'category': 'Unknown / General',
                          'purpose': 'FFMPEG wrapper for Python',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'importlib_metadata': {   'category': 'Data Analysis',
                              'purpose': 'Read metadata from Python packages',
                              'use_cases': [   'Potentially used for data '
                                               'analysis tasks.']},
    'importlib_resources': {   'category': 'Unknown / General',
                               'purpose': 'Read resources from Python packages',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'iniconfig': {   'category': 'Machine Learning',
                     'purpose': 'brain-dead simple config-ini parsing',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'inquirer': {   'category': 'Unknown / General',
                    'purpose': 'Collection of common interactive command line '
                               'user interfaces, based on Inquirer.js',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'instructor': {   'category': 'Unknown / General',
                      'purpose': 'structured outputs for llm',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ipykernel': {   'category': 'Web Framework',
                     'purpose': 'IPython Kernel for Jupyter',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'ipython': {   'category': 'Unknown / General',
                   'purpose': 'IPython: Productive Interactive Computing',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'ipython_pygments_lexers': {   'category': 'Unknown / General',
                                   'purpose': 'Defines a variety of Pygments '
                                              'lexers for highlighting IPython '
                                              'code.',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'ipywidgets': {   'category': 'Web Framework',
                      'purpose': 'Jupyter interactive widgets',
                      'use_cases': [   'Potentially used for web framework '
                                       'tasks.']},
    'isoduration': {   'category': 'Unknown / General',
                       'purpose': 'Operations with ISO 8601 durations',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'itsdangerous': {   'category': 'Data Analysis',
                        'purpose': 'Safely pass data to untrusted environments '
                                   'and back.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'jax': {   'category': 'Database / Storage',
               'purpose': 'Differentiate, compile, and transform Numpy code.',
               'use_cases': ['Potentially used for database / storage tasks.']},
    'jaxlib': {   'category': 'Unknown / General',
                  'purpose': 'XLA library for JAX',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jaxopt': {   'category': 'Unknown / General',
                  'purpose': 'Hardware accelerated, batchable and '
                             'differentiable optimizers in JAX.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jedi': {   'category': 'Unknown / General',
                'purpose': 'An autocompletion tool for Python that can be used '
                           'for text editors.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'jinja2': {   'category': 'Unknown / General',
                  'purpose': 'A very fast and expressive template engine.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jiter': {   'category': 'Unknown / General',
                 'purpose': 'Fast iterable JSON parser.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'joblib': {   'category': 'Unknown / General',
                  'purpose': 'Lightweight pipelining with Python functions',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'json-tricks': {   'category': 'Data Analysis',
                       'purpose': "Extra features for Python's JSON: comments, "
                                  'order, numpy, pandas, datetimes, and many '
                                  'more! Simple but customizable.',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'json5': {   'category': 'Data Analysis',
                 'purpose': 'A Python implementation of the JSON5 data format.',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'json_repair': {   'category': 'Machine Learning',
                       'purpose': 'A package to repair broken json strings',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'jsonpatch': {   'category': 'Unknown / General',
                     'purpose': 'Apply JSON-Patches (RFC 6902)',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'jsonpickle': {   'category': 'Unknown / General',
                      'purpose': 'jsonpickle encodes/decodes any Python object '
                                 'to/from JSON',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'jsonpointer': {   'category': 'Unknown / General',
                       'purpose': 'Identify specific nodes in a JSON document '
                                  '(RFC 6901)',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'jsonref': {   'category': 'Unknown / General',
                   'purpose': 'jsonref is a library for automatic '
                              'dereferencing of JSON Reference objects for '
                              'Python.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'jsonschema': {   'category': 'Data Analysis',
                      'purpose': 'An implementation of JSON Schema validation '
                                 'for Python',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'jsonschema-specifications': {   'category': 'Data Analysis',
                                     'purpose': 'The JSON Schema meta-schemas '
                                                'and vocabularies, exposed as '
                                                'a Registry',
                                     'use_cases': [   'Potentially used for '
                                                      'data analysis tasks.']},
    'jupyter': {   'category': 'Unknown / General',
                   'purpose': 'Jupyter metapackage. Install all the Jupyter '
                              'components in one go.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'jupyter-console': {   'category': 'Web Framework',
                           'purpose': 'Jupyter terminal console',
                           'use_cases': [   'Potentially used for web '
                                            'framework tasks.']},
    'jupyter-events': {   'category': 'Unknown / General',
                          'purpose': 'Jupyter Event System library',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'jupyter-lsp': {   'category': 'Web Framework',
                       'purpose': 'Multi-Language Server WebSocket proxy for '
                                  'Jupyter Notebook/Lab server',
                       'use_cases': [   'Potentially used for web framework '
                                        'tasks.']},
    'jupyter_client': {   'category': 'Web Framework',
                          'purpose': 'Jupyter protocol implementation and '
                                     'client libraries',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'jupyter_core': {   'category': 'Unknown / General',
                        'purpose': 'Jupyter core package. A base package on '
                                   'which Jupyter projects rely.',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'jupyter_server': {   'category': 'Web Framework',
                          'purpose': 'The backend—i.e. core services, APIs, '
                                     'and REST endpoints—to Jupyter web '
                                     'applications.',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'jupyter_server_terminals': {   'category': 'Unknown / General',
                                    'purpose': 'A Jupyter Server Extension '
                                               'Providing Terminals.',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'jupyterlab': {   'category': 'Unknown / General',
                      'purpose': 'JupyterLab computational environment',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'jupyterlab_pygments': {   'category': 'Unknown / General',
                               'purpose': 'Pygments theme using JupyterLab CSS '
                                          'variables',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'jupyterlab_server': {   'category': 'Unknown / General',
                             'purpose': 'A set of server components for '
                                        'JupyterLab and JupyterLab like '
                                        'applications.',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'jupyterlab_widgets': {   'category': 'Web Framework',
                              'purpose': 'Jupyter interactive widgets for '
                                         'JupyterLab',
                              'use_cases': [   'Potentially used for web '
                                               'framework tasks.']},
    'kiwisolver': {   'category': 'Machine Learning',
                      'purpose': 'A fast implementation of the Cassowary '
                                 'constraint solver',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'kubernetes': {   'category': 'Web Framework',
                      'purpose': 'Kubernetes python client',
                      'use_cases': [   'Potentially used for web framework '
                                       'tasks.']},
    'langchain': {   'category': 'Unknown / General',
                     'purpose': 'Building applications with LLMs through '
                                'composability',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'langchain-core': {   'category': 'Unknown / General',
                          'purpose': 'Building applications with LLMs through '
                                     'composability',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'langchain-text-splitters': {   'category': 'Machine Learning',
                                    'purpose': 'LangChain text splitting '
                                               'utilities',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'langcodes': {   'category': 'Unknown / General',
                     'purpose': 'Tools for labeling human languages with IETF '
                                'language tags',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'langgraph': {   'category': 'Unknown / General',
                     'purpose': 'Building stateful, multi-actor applications '
                                'with LLMs',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'langgraph-checkpoint': {   'category': 'Visualization',
                                'purpose': 'Library with base interfaces for '
                                           'LangGraph checkpoint savers.',
                                'use_cases': [   'Potentially used for '
                                                 'visualization tasks.']},
    'langgraph-prebuilt': {   'category': 'Web Framework',
                              'purpose': 'Library with high-level APIs for '
                                         'creating and executing LangGraph '
                                         'agents and tools.',
                              'use_cases': [   'Potentially used for web '
                                               'framework tasks.']},
    'langgraph-sdk': {   'category': 'Web Framework',
                         'purpose': 'SDK for interacting with LangGraph API',
                         'use_cases': [   'Potentially used for web framework '
                                          'tasks.']},
    'langsmith': {   'category': 'Machine Learning',
                     'purpose': 'Client library to connect to the LangSmith '
                                'LLM Tracing and Evaluation Platform.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'language_data': {   'category': 'Data Analysis',
                         'purpose': 'Supplementary data about languages used '
                                    'by the langcodes module',
                         'use_cases': [   'Potentially used for data analysis '
                                          'tasks.']},
    'lark': {   'category': 'Unknown / General',
                'purpose': 'a modern parsing library',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'lazy_loader': {   'category': 'Unknown / General',
                       'purpose': 'Makes it easy to load subpackages and '
                                  'functions on demand.',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'leabra-psyneulink': {   'category': 'Unknown / General',
                             'purpose': 'Python implementation of the Leabra '
                                        'algorithm. Forked to package and '
                                        'upload to PyPi.',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'librosa': {   'category': 'Unknown / General',
                   'purpose': 'Python module for audio and music processing',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'lightning-utilities': {   'category': 'Unknown / General',
                               'purpose': 'Lightning toolbox for across the '
                                          'our ecosystem.',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'litellm': {   'category': 'Web Framework',
                   'purpose': 'Library to easily interface with LLM API '
                              'providers',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'llama-cloud': {   'category': 'Unknown / General',
                       'purpose': 'Auto-discovered Python library named '
                                  "'llama-cloud'. Purpose not yet documented.",
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'llama-cloud-services': {   'category': 'Machine Learning',
                                'purpose': 'Tailored SDK clients for '
                                           'LlamaCloud services.',
                                'use_cases': [   'Potentially used for machine '
                                                 'learning tasks.']},
    'llama-index': {   'category': 'Data Analysis',
                       'purpose': 'Interface between LLMs and your data',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'llama-index-cli': {   'category': 'Unknown / General',
                           'purpose': 'llama-index cli',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'llama-index-core': {   'category': 'Data Analysis',
                            'purpose': 'Interface between LLMs and your data',
                            'use_cases': [   'Potentially used for data '
                                             'analysis tasks.']},
    'llama-index-embeddings-openai': {   'category': 'Machine Learning',
                                         'purpose': 'llama-index embeddings '
                                                    'openai integration',
                                         'use_cases': [   'Potentially used '
                                                          'for machine '
                                                          'learning tasks.']},
    'llama-index-indices-managed-llama-cloud': {   'category': 'Unknown / '
                                                               'General',
                                                   'purpose': 'llama-index '
                                                              'indices '
                                                              'llama-cloud '
                                                              'integration',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'unknown / '
                                                                    'general '
                                                                    'tasks.']},
    'llama-index-instrumentation': {   'category': 'Unknown / General',
                                       'purpose': 'Add your description here',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'llama-index-llms-openai': {   'category': 'Machine Learning',
                                   'purpose': 'llama-index llms openai '
                                              'integration',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'llama-index-readers-file': {   'category': 'Machine Learning',
                                    'purpose': 'llama-index readers file '
                                               'integration',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'llama-index-readers-llama-parse': {   'category': 'Unknown / General',
                                           'purpose': 'llama-index readers '
                                                      'llama-parse integration',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'llama-index-workflows': {   'category': 'Machine Learning',
                                 'purpose': 'An event-driven, async-first, '
                                            'step-based way to control the '
                                            'execution flow of AI applications '
                                            'like Agents.',
                                 'use_cases': [   'Potentially used for '
                                                  'machine learning tasks.']},
    'llama-parse': {   'category': 'Database / Storage',
                       'purpose': 'Parse files into RAG-Optimized formats.',
                       'use_cases': [   'Potentially used for database / '
                                        'storage tasks.']},
    'llama_cpp_python': {   'category': 'Unknown / General',
                            'purpose': 'Python bindings for the llama.cpp '
                                       'library',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'llvmlite': {   'category': 'Unknown / General',
                    'purpose': 'lightweight wrapper around basic LLVM '
                               'functionality',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'logical-unification': {   'category': 'Unknown / General',
                               'purpose': 'Logical unification in Python',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'loguru': {   'category': 'Unknown / General',
                  'purpose': 'Python logging made (stupidly) simple',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'magicattr': {   'category': 'Unknown / General',
                     'purpose': 'A getattr and setattr that works on nested '
                                'objects, lists, dicts, and any combination '
                                'thereof without resorting to eval',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'mako': {   'category': 'Unknown / General',
                'purpose': 'A super-fast templating language that borrows the '
                           'best ideas from the existing templating languages.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'marisa-trie': {   'category': 'Unknown / General',
                       'purpose': 'Static memory-efficient and fast Trie-like '
                                  'structures for Python.',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'markdown': {   'category': 'Machine Learning',
                    'purpose': "Python implementation of John Gruber's "
                               'Markdown.',
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'markdown-it-py': {   'category': 'Unknown / General',
                          'purpose': 'Python port of markdown-it. Markdown '
                                     'parsing, done right!',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'markupsafe': {   'category': 'Machine Learning',
                      'purpose': 'Safely add untrusted strings to HTML/XML '
                                 'markup.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'marshmallow': {   'category': 'Data Analysis',
                       'purpose': 'A lightweight library for converting '
                                  'complex datatypes to and from native Python '
                                  'datatypes.',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'matplotlib': {   'category': 'Visualization',
                      'purpose': 'Python plotting package',
                      'use_cases': [   'Potentially used for visualization '
                                       'tasks.']},
    'matplotlib-inline': {   'category': 'Visualization',
                             'purpose': 'Inline Matplotlib backend for Jupyter',
                             'use_cases': [   'Potentially used for '
                                              'visualization tasks.']},
    'mdurl': {   'category': 'Unknown / General',
                 'purpose': 'Markdown URL utilities',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'mediadecoder': {   'category': 'Unknown / General',
                        'purpose': 'Media-decoding library based on MoviePy',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'mediapipe': {   'category': 'Machine Learning',
                     'purpose': 'MediaPipe is the simplest way for researchers '
                                'and developers to build world-class ML '
                                'solutions and applications for mobile, edge, '
                                'cloud and the web.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'meshpy': {   'category': 'Unknown / General',
                  'purpose': 'Triangular and Tetrahedral Mesh Generator',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'minikanren': {   'category': 'Unknown / General',
                      'purpose': 'Relational programming in Python',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'mistune': {   'category': 'Unknown / General',
                   'purpose': 'A sane and fast Markdown parser with useful '
                              'plugins and renderers',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'ml_dtypes': {   'category': 'Machine Learning',
                     'purpose': 'ml_dtypes is a stand-alone implementation of '
                                'several NumPy dtype extensions used in '
                                'machine learning.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'mmh3': {   'category': 'Unknown / General',
                'purpose': 'Python extension for MurmurHash (MurmurHash3), a '
                           'set of fast and robust hash functions.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'mne': {   'category': 'Machine Learning',
               'purpose': 'MNE-Python project for MEG and EEG data analysis.',
               'use_cases': ['Potentially used for machine learning tasks.']},
    'modeci-mdf': {   'category': 'Database / Storage',
                      'purpose': 'ModECI (Model Exchange and Convergence '
                                 'Initiative) Model Description Format',
                      'use_cases': [   'Potentially used for database / '
                                       'storage tasks.']},
    'modelspec': {   'category': 'Machine Learning',
                     'purpose': 'A common JSON/YAML based format for compact '
                                'model specification',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'more-itertools': {   'category': 'Unknown / General',
                          'purpose': 'More routines for operating on '
                                     'iterables, beyond itertools',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'moviepy': {   'category': 'Unknown / General',
                   'purpose': 'Video editing with Python',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'mpmath': {   'category': 'Unknown / General',
                  'purpose': 'Python library for arbitrary-precision '
                             'floating-point arithmetic',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'msgpack': {   'category': 'Unknown / General',
                   'purpose': 'MessagePack serializer',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'msgpack-numpy': {   'category': 'Data Analysis',
                         'purpose': 'Numpy data serialization using msgpack',
                         'use_cases': [   'Potentially used for data analysis '
                                          'tasks.']},
    'multidict': {   'category': 'Unknown / General',
                     'purpose': 'multidict implementation',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'multipledispatch': {   'category': 'Unknown / General',
                            'purpose': 'Multiple dispatch',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'multiprocess': {   'category': 'Unknown / General',
                        'purpose': 'better multiprocessing and multithreading '
                                   'in Python',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'munkres': {   'category': 'Unknown / General',
                   'purpose': 'Munkres (Hungarian) algorithm for the '
                              'Assignment Problem',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'murmurhash': {   'category': 'Unknown / General',
                      'purpose': 'Cython bindings for MurmurHash',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'mypy_extensions': {   'category': 'Unknown / General',
                           'purpose': 'Type system extensions for programs '
                                      'checked with the mypy type checker.',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'narwhals': {   'category': 'Data Analysis',
                    'purpose': 'Extremely lightweight compatibility layer '
                               'between dataframe libraries',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'nbclient': {   'category': 'Database / Storage',
                    'purpose': 'A client library for executing notebooks. '
                               "Formerly nbconvert's ExecutePreprocessor.",
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'nbconvert': {   'category': 'Machine Learning',
                     'purpose': 'Converting Jupyter Notebooks (.ipynb files) '
                                'to other formats.  Output formats include '
                                'asciidoc, html, latex, markdown, pdf, py, '
                                'rst, script.  nbconvert can be used both as a '
                                'Python library (`import nbconvert`) or as a '
                                'command line tool (invoked as `jupyter '
                                'nbconvert ...`).',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'nbformat': {   'category': 'Web Framework',
                    'purpose': 'The Jupyter Notebook format',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'ndindex': {   'category': 'Unknown / General',
                   'purpose': 'A Python library for manipulating indices of '
                              'ndarrays.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'nengo': {   'category': 'Machine Learning',
                 'purpose': 'Tools for building and simulating large-scale '
                            'neural models',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'nest-asyncio': {   'category': 'Networking',
                        'purpose': 'Patch asyncio to allow nested event loops',
                        'use_cases': [   'Potentially used for networking '
                                         'tasks.']},
    'networkx': {   'category': 'Visualization',
                    'purpose': 'Python package for creating and manipulating '
                               'graphs and networks',
                    'use_cases': ['Potentially used for visualization tasks.']},
    'neurokit2': {   'category': 'Unknown / General',
                     'purpose': 'The Python Toolbox for Neurophysiological '
                                'Signal Processing.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'nibabel': {   'category': 'Data Analysis',
                   'purpose': 'Access a multitude of neuroimaging data formats',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'nilearn': {   'category': 'Unknown / General',
                   'purpose': 'Statistical learning for neuroimaging in Python',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'nltk': {   'category': 'Unknown / General',
                'purpose': 'Natural Language Toolkit',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'nodeenv': {   'category': 'Unknown / General',
                   'purpose': 'Node.js virtual environment builder',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'noisereduce': {   'category': 'Unknown / General',
                       'purpose': 'Noise reduction using Spectral Gating in '
                                  'Python',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'nose': {   'category': 'Unknown / General',
                'purpose': 'nose extends unittest to make testing easier',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'notebook': {   'category': 'Web Framework',
                    'purpose': 'Jupyter Notebook - A web-based notebook '
                               'environment for interactive computing',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'notebook_shim': {   'category': 'Machine Learning',
                         'purpose': 'A shim layer for notebook traits and '
                                    'config',
                         'use_cases': [   'Potentially used for machine '
                                          'learning tasks.']},
    'numba': {   'category': 'Unknown / General',
                 'purpose': 'compiling Python code using LLVM',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'numexpr': {   'category': 'Unknown / General',
                   'purpose': 'Fast numerical expression evaluator for NumPy',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'numpy': {   'category': 'Unknown / General',
                 'purpose': 'Fundamental package for array computing in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'oauthlib': {   'category': 'Security / Encryption',
                    'purpose': 'A generic, spec-compliant, thorough '
                               'implementation of the OAuth request-signing '
                               'logic',
                    'use_cases': [   'Potentially used for security / '
                                     'encryption tasks.']},
    'omegaconf': {   'category': 'Machine Learning',
                     'purpose': 'A flexible configuration library',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'onnx': {   'category': 'Machine Learning',
                'purpose': 'Open Neural Network Exchange',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'onnxruntime': {   'category': 'Unknown / General',
                       'purpose': 'ONNX Runtime is a runtime accelerator for '
                                  'Machine Learning models',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'open-interpreter': {   'category': 'Unknown / General',
                            'purpose': 'Let language models run code',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'openai': {   'category': 'Machine Learning',
                  'purpose': 'The official Python library for the openai API',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'openai-whisper': {   'category': 'Unknown / General',
                          'purpose': 'Robust Speech Recognition via '
                                     'Large-Scale Weak Supervision',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'opencv-contrib-python': {   'category': 'Unknown / General',
                                 'purpose': 'Wrapper package for OpenCV python '
                                            'bindings.',
                                 'use_cases': [   'Potentially used for '
                                                  'unknown / general tasks.']},
    'opencv-python': {   'category': 'Unknown / General',
                         'purpose': 'Wrapper package for OpenCV python '
                                    'bindings.',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'openpyxl': {   'category': 'Data Analysis',
                    'purpose': 'A Python library to read/write Excel 2010 '
                               'xlsx/xlsm files',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'opentelemetry-api': {   'category': 'Web Framework',
                             'purpose': 'OpenTelemetry Python API',
                             'use_cases': [   'Potentially used for web '
                                              'framework tasks.']},
    'opentelemetry-exporter-otlp-proto-common': {   'category': 'Unknown / '
                                                                'General',
                                                    'purpose': 'OpenTelemetry '
                                                               'Protobuf '
                                                               'encoding',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'unknown '
                                                                     '/ '
                                                                     'general '
                                                                     'tasks.']},
    'opentelemetry-exporter-otlp-proto-grpc': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'OpenTelemetry '
                                                             'Collector '
                                                             'Protobuf over '
                                                             'gRPC Exporter',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'opentelemetry-exporter-otlp-proto-http': {   'category': 'Networking',
                                                  'purpose': 'OpenTelemetry '
                                                             'Collector '
                                                             'Protobuf over '
                                                             'HTTP Exporter',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'networking '
                                                                   'tasks.']},
    'opentelemetry-proto': {   'category': 'Unknown / General',
                               'purpose': 'OpenTelemetry Python Proto',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'opentelemetry-sdk': {   'category': 'Unknown / General',
                             'purpose': 'OpenTelemetry Python SDK',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'opentelemetry-semantic-conventions': {   'category': 'Unknown / General',
                                              'purpose': 'OpenTelemetry '
                                                         'Semantic Conventions',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'opt_einsum': {   'category': 'Unknown / General',
                      'purpose': 'Path optimization of einsum functions.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'optree': {   'category': 'Unknown / General',
                  'purpose': 'Optimized PyTree Utilities.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'optuna': {   'category': 'Unknown / General',
                  'purpose': 'A hyperparameter optimization framework',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'orjson': {   'category': 'Data Analysis',
                  'purpose': 'Fast, correct Python JSON library supporting '
                             'dataclasses, datetimes, and numpy',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'ormsgpack': {   'category': 'Database / Storage',
                     'purpose': 'Auto-discovered Python library named '
                                "'ormsgpack'. Purpose not yet documented.",
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'osqp': {   'category': 'Unknown / General',
                'purpose': 'OSQP: The Operator Splitting QP Solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'outcome': {   'category': 'Unknown / General',
                   'purpose': 'Capture the outcome of Python function calls.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'overrides': {   'category': 'Unknown / General',
                     'purpose': 'A decorator to automatically detect mismatch '
                                'when overriding a method.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'packaging': {   'category': 'Unknown / General',
                     'purpose': 'Core utilities for Python packages',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pandas': {   'category': 'Data Analysis',
                  'purpose': 'Powerful data structures for data analysis, time '
                             'series, and statistics',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'pandocfilters': {   'category': 'Unknown / General',
                         'purpose': 'Utilities for writing pandoc filters in '
                                    'python',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'parso': {   'category': 'Unknown / General',
                 'purpose': 'A Python Parser',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'patsy': {   'category': 'Unknown / General',
                 'purpose': 'A Python package for describing statistical '
                            'models and for building design matrices.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'pdfminer.six': {   'category': 'Unknown / General',
                        'purpose': 'PDF parser and analyzer',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'pdfplumber': {   'category': 'Machine Learning',
                      'purpose': 'Plumb a PDF for detailed information about '
                                 'each char, rectangle, and line.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'pexpect': {   'category': 'Unknown / General',
                   'purpose': 'Pexpect allows easy control of interactive '
                              'console applications.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'pgmpy': {   'category': 'Visualization',
                 'purpose': 'A library for Probabilistic Graphical Models',
                 'use_cases': ['Potentially used for visualization tasks.']},
    'pickleshare': {   'category': 'Data Analysis',
                       'purpose': "Tiny 'shelve'-like database with "
                                  'concurrency support',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'pillow': {   'category': 'Unknown / General',
                  'purpose': 'Python Imaging Library (Fork)',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pint': {   'category': 'Unknown / General',
                'purpose': 'Physical quantities module',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'pip': {   'category': 'Unknown / General',
               'purpose': 'The PyPA recommended tool for installing Python '
                          'packages.',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'piqp': {   'category': 'Unknown / General',
                'purpose': 'A Proximal Interior Point Quadratic Programming '
                           'solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'platformdirs': {   'category': 'Data Analysis',
                        'purpose': 'A small Python package for determining '
                                   'appropriate platform-specific dirs, e.g. a '
                                   '`user data dir`.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'pluggy': {   'category': 'Unknown / General',
                  'purpose': 'plugin and hook calling mechanisms for python',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pomegranate': {   'category': 'Machine Learning',
                       'purpose': 'A PyTorch implementation of probabilistic '
                                  'models.',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'pooch': {   'category': 'Data Analysis',
                 'purpose': 'A friend to fetch your data files',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'posthog': {   'category': 'Unknown / General',
                   'purpose': 'Integrate PostHog into any python application.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'pre_commit': {   'category': 'Machine Learning',
                      'purpose': 'A framework for managing and maintaining '
                                 'multi-language pre-commit hooks.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'preshed': {   'category': 'Unknown / General',
                   'purpose': 'Cython hash table that trusts the keys are '
                              'pre-hashed',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'proglog': {   'category': 'Web Framework',
                   'purpose': 'Log and progress bar manager for console, '
                              'notebooks, web...',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'prometheus_client': {   'category': 'Unknown / General',
                             'purpose': 'Python client for the Prometheus '
                                        'monitoring system.',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'prompt_toolkit': {   'category': 'Unknown / General',
                          'purpose': 'Library for building powerful '
                                     'interactive command lines in Python',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'propcache': {   'category': 'Unknown / General',
                     'purpose': 'Accelerated property cache',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'proto-plus': {   'category': 'Unknown / General',
                      'purpose': 'Beautiful, Pythonic protocol buffers',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'protobuf': {   'category': 'Unknown / General',
                    'purpose': 'Auto-discovered Python library named '
                               "'protobuf'. Purpose not yet documented.",
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'proxsuite': {   'category': 'Unknown / General',
                     'purpose': 'Quadratic Programming Solver for Robotics and '
                                'beyond.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'psutil': {   'category': 'Database / Storage',
                  'purpose': 'Cross-platform lib for process and system '
                             'monitoring in Python.',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'psychopy': {   'category': 'Unknown / General',
                    'purpose': 'PsychoPy provides easy, precise, flexible '
                               'experiments in behavioural sciences',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'psychtoolbox': {   'category': 'Unknown / General',
                        'purpose': 'Pieces of Psychtoolbox-3 ported to '
                                   'CPython.',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'psyneulink': {   'category': 'Unknown / General',
                      'purpose': 'A block modeling system for cognitive '
                                 'neuroscience',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ptyprocess': {   'category': 'Unknown / General',
                      'purpose': 'Run a subprocess in a pseudo terminal',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'pure_eval': {   'category': 'Unknown / General',
                     'purpose': 'Safely evaluate AST nodes without side '
                                'effects',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'py-cpuinfo': {   'category': 'Unknown / General',
                      'purpose': 'Get CPU info with pure Python',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'pyarrow': {   'category': 'Unknown / General',
                   'purpose': 'Python library for Apache Arrow',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'pyasn1': {   'category': 'Unknown / General',
                  'purpose': 'Pure-Python implementation of ASN.1 types and '
                             'DER/BER/CER codecs (X.208)',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyasn1_modules': {   'category': 'Unknown / General',
                          'purpose': 'A collection of ASN.1-based protocols '
                                     'modules',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'pyaudio': {   'category': 'Database / Storage',
                   'purpose': 'Cross-platform audio I/O with PortAudio',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'pyautogen': {   'category': 'Machine Learning',
                     'purpose': 'A programming framework for agentic AI. Proxy '
                                'package for autogen-agentchat.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pybase64': {   'category': 'Unknown / General',
                    'purpose': 'Fast Base64 encoding/decoding',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pybind11': {   'category': 'Machine Learning',
                    'purpose': 'Seamless operability between C++11 and Python',
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'pybind11-global': {   'category': 'Machine Learning',
                           'purpose': 'Seamless operability between C++11 and '
                                      'Python',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'pycparser': {   'category': 'Unknown / General',
                     'purpose': 'C parser in Python',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pydantic': {   'category': 'Data Analysis',
                    'purpose': 'Data validation using Python type hints',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'pydantic_core': {   'category': 'Unknown / General',
                         'purpose': 'Core functionality for Pydantic '
                                    'validation and serialization',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'pydatalog': {   'category': 'Machine Learning',
                     'purpose': 'A pure-python implementation of Datalog, a '
                                'truly declarative language derived from '
                                'Prolog.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pydub': {   'category': 'Unknown / General',
                 'purpose': 'Manipulate audio with an simple and easy high '
                            'level interface',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'pyenchant': {   'category': 'Unknown / General',
                     'purpose': 'Python bindings for the Enchant spellchecking '
                                'system',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pygame': {   'category': 'Unknown / General',
                  'purpose': 'Python Game Development',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pygaze': {   'category': 'Unknown / General',
                  'purpose': 'pygaze is a gaze estimation framework for python '
                             'based on eth-xgaze.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyglet': {   'category': 'Database / Storage',
                  'purpose': 'Cross-platform windowing and multimedia library',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'pygments': {   'category': 'Unknown / General',
                    'purpose': 'Pygments is a syntax highlighting package '
                               'written in Python.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pyjwt': {   'category': 'Web Framework',
                 'purpose': 'JSON Web Token implementation in Python',
                 'use_cases': ['Potentially used for web framework tasks.']},
    'pymc': {   'category': 'Unknown / General',
                'purpose': 'Probabilistic Programming in Python: Bayesian '
                           'Modeling and Probabilistic Machine Learning with '
                           'PyTensor',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'pymdp': {   'category': 'Unknown / General',
                 'purpose': 'Markov decision processes in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'pymongo': {   'category': 'Unknown / General',
                   'purpose': 'PyMongo - the Official MongoDB Python driver',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'pynput': {   'category': 'Unknown / General',
                  'purpose': 'Monitor and control user input devices',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyobjc': {   'category': 'Unknown / General',
                  'purpose': 'Python<->ObjC Interoperability Module',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyobjc-core': {   'category': 'Unknown / General',
                       'purpose': 'Python<->ObjC Interoperability Module',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'pyobjc-framework-accessibility': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework Accessibility '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-accounts': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Accounts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-addressbook': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'AddressBook on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-adservices': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'AdServices on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-adsupport': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'AdSupport on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-applescriptkit': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'AppleScriptKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-applescriptobjc': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'AppleScriptObjC on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-applicationservices': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'ApplicationServices '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-apptrackingtransparency': {   'category': 'Unknown / '
                                                                'General',
                                                    'purpose': 'Wrappers for '
                                                               'the framework '
                                                               'AppTrackingTransparency '
                                                               'on macOS',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'unknown '
                                                                     '/ '
                                                                     'general '
                                                                     'tasks.']},
    'pyobjc-framework-audiovideobridging': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'AudioVideoBridging '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-authenticationservices': {   'category': 'Security / '
                                                               'Encryption',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'AuthenticationServices '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'security '
                                                                    '/ '
                                                                    'encryption '
                                                                    'tasks.']},
    'pyobjc-framework-automaticassessmentconfiguration': {   'category': 'Unknown '
                                                                         '/ '
                                                                         'General',
                                                             'purpose': 'Wrappers '
                                                                        'for '
                                                                        'the '
                                                                        'framework '
                                                                        'AutomaticAssessmentConfiguration '
                                                                        'on '
                                                                        'macOS',
                                                             'use_cases': [   'Potentially '
                                                                              'used '
                                                                              'for '
                                                                              'unknown '
                                                                              '/ '
                                                                              'general '
                                                                              'tasks.']},
    'pyobjc-framework-automator': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Automator on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-avfoundation': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework AVFoundation on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-avkit': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework AVKit '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-avrouting': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'AVRouting on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-backgroundassets': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'BackgroundAssets on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-browserenginekit': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'BrowserEngineKit on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-businesschat': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework BusinessChat on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-calendarstore': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CalendarStore '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-callkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'CallKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-carbon': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Carbon on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-cfnetwork': {   'category': 'Networking',
                                      'purpose': 'Wrappers for the framework '
                                                 'CFNetwork on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'networking tasks.']},
    'pyobjc-framework-cinematic': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Cinematic on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-classkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'ClassKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cloudkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CloudKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cocoa': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the Cocoa '
                                             'frameworks on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-collaboration': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework Collaboration '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-colorsync': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ColorSync on Mac OS X',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-contacts': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Contacts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-contactsui': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'ContactsUI on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-coreaudio': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'CoreAudio on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-coreaudiokit': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreAudioKit on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-corebluetooth': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CoreBluetooth '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-coredata': {   'category': 'Data Analysis',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreData on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'data analysis tasks.']},
    'pyobjc-framework-corehaptics': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'CoreHaptics on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-corelocation': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreLocation on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-coremedia': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'CoreMedia on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-coremediaio': {   'category': 'Machine Learning',
                                        'purpose': 'Wrappers for the framework '
                                                   'CoreMediaIO on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'machine learning '
                                                         'tasks.']},
    'pyobjc-framework-coremidi': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreMIDI on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-coreml': {   'category': 'Machine Learning',
                                   'purpose': 'Wrappers for the framework '
                                              'CoreML on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'pyobjc-framework-coremotion': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'CoreMotion on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-coreservices': {   'category': 'Data Analysis',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreServices on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for data analysis '
                                                          'tasks.']},
    'pyobjc-framework-corespotlight': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CoreSpotlight '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-coretext': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreText on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-corewlan': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreWLAN on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cryptotokenkit': {   'category': 'Security / Encryption',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'CryptoTokenKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for security / '
                                                            'encryption '
                                                            'tasks.']},
    'pyobjc-framework-datadetection': {   'category': 'Data Analysis',
                                          'purpose': 'Wrappers for the '
                                                     'framework DataDetection '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for data analysis '
                                                           'tasks.']},
    'pyobjc-framework-devicecheck': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'DeviceCheck on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-devicediscoveryextension': {   'category': 'Unknown / '
                                                                 'General',
                                                     'purpose': 'Wrappers for '
                                                                'the framework '
                                                                'DeviceDiscoveryExtension '
                                                                'on macOS',
                                                     'use_cases': [   'Potentially '
                                                                      'used '
                                                                      'for '
                                                                      'unknown '
                                                                      '/ '
                                                                      'general '
                                                                      'tasks.']},
    'pyobjc-framework-dictionaryservices': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'DictionaryServices '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-discrecording': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework DiscRecording '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-discrecordingui': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'DiscRecordingUI on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-diskarbitration': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'DiskArbitration on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-dvdplayback': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'DVDPlayback on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-eventkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Accounts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-exceptionhandling': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ExceptionHandling on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-executionpolicy': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'ExecutionPolicy on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-extensionkit': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework ExtensionKit on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-externalaccessory': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ExternalAccessory on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-fileprovider': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework FileProvider on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-fileproviderui': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'FileProviderUI on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-findersync': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'FinderSync on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-fsevents': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'FSEvents on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-fskit': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework FSKit '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-gamecenter': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'GameCenter on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-gamecontroller': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'GameController on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-gamekit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'GameKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-gameplaykit': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'GameplayKit on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-healthkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'HealthKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-imagecapturecore': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'ImageCaptureCore on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-inputmethodkit': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'InputMethodKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-installerplugins': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'InstallerPlugins on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-instantmessage': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'InstantMessage on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-intents': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'Intents on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-intentsui': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Intents on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-iobluetooth': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'IOBluetooth on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-iobluetoothui': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework IOBluetoothUI '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-iosurface': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'IOSurface on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-ituneslibrary': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework iTunesLibrary '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-kernelmanagement': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'KernelManagement on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-latentsemanticmapping': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'LatentSemanticMapping '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'pyobjc-framework-launchservices': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'LaunchServices on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-libdispatch': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for libdispatch '
                                                   'on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-libxpc': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for xpc on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-linkpresentation': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'LinkPresentation on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-localauthentication': {   'category': 'Security / '
                                                            'Encryption',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'LocalAuthentication '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'security / '
                                                                 'encryption '
                                                                 'tasks.']},
    'pyobjc-framework-localauthenticationembeddedui': {   'category': 'Security '
                                                                      '/ '
                                                                      'Encryption',
                                                          'purpose': 'Wrappers '
                                                                     'for the '
                                                                     'framework '
                                                                     'LocalAuthenticationEmbeddedUI '
                                                                     'on macOS',
                                                          'use_cases': [   'Potentially '
                                                                           'used '
                                                                           'for '
                                                                           'security '
                                                                           '/ '
                                                                           'encryption '
                                                                           'tasks.']},
    'pyobjc-framework-mailkit': {   'category': 'Machine Learning',
                                    'purpose': 'Wrappers for the framework '
                                               'MailKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'pyobjc-framework-mapkit': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'MapKit on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-mediaaccessibility': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'MediaAccessibility '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-mediaextension': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'MediaExtension on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-medialibrary': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework MediaLibrary on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-mediaplayer': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'MediaPlayer on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-mediatoolbox': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework MediaToolbox on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-metal': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework Metal '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-metalfx': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'MetalFX on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-metalkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'MetalKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-metalperformanceshaders': {   'category': 'Database / '
                                                                'Storage',
                                                    'purpose': 'Wrappers for '
                                                               'the framework '
                                                               'MetalPerformanceShaders '
                                                               'on macOS',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'database '
                                                                     '/ '
                                                                     'storage '
                                                                     'tasks.']},
    'pyobjc-framework-metalperformanceshadersgraph': {   'category': 'Visualization',
                                                         'purpose': 'Wrappers '
                                                                    'for the '
                                                                    'framework '
                                                                    'MetalPerformanceShadersGraph '
                                                                    'on macOS',
                                                         'use_cases': [   'Potentially '
                                                                          'used '
                                                                          'for '
                                                                          'visualization '
                                                                          'tasks.']},
    'pyobjc-framework-metrickit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'MetricKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-mlcompute': {   'category': 'Machine Learning',
                                      'purpose': 'Wrappers for the framework '
                                                 'MLCompute on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'machine learning '
                                                       'tasks.']},
    'pyobjc-framework-modelio': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'ModelIO on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-multipeerconnectivity': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'MultipeerConnectivity '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'pyobjc-framework-naturallanguage': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'NaturalLanguage on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-netfs': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework NetFS '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-network': {   'category': 'Networking',
                                    'purpose': 'Wrappers for the framework '
                                               'Network on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'networking tasks.']},
    'pyobjc-framework-networkextension': {   'category': 'Networking',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'NetworkExtension on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'networking '
                                                              'tasks.']},
    'pyobjc-framework-notificationcenter': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'NotificationCenter '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-opendirectory': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework OpenDirectory '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-osakit': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'OSAKit on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-oslog': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework OSLog '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-passkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'PassKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-pencilkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'PencilKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-phase': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework PHASE '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-photos': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Photos on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-photosui': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'PhotosUI on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-preferencepanes': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'PreferencePanes on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-pushkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'PushKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-quartz': {   'category': 'Visualization',
                                   'purpose': 'Wrappers for the Quartz '
                                              'frameworks on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'visualization tasks.']},
    'pyobjc-framework-quicklookthumbnailing': {   'category': 'Machine '
                                                              'Learning',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'QuickLookThumbnailing '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'machine '
                                                                   'learning '
                                                                   'tasks.']},
    'pyobjc-framework-replaykit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ReplayKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-safariservices': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'SafariServices on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-safetykit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SafetyKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-scenekit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'SceneKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-screencapturekit': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'ScreenCaptureKit on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-screensaver': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'ScreenSaver on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-screentime': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'ScreenTime on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-scriptingbridge': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'ScriptingBridge on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-searchkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SearchKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-security': {   'category': 'Security / Encryption',
                                     'purpose': 'Wrappers for the framework '
                                                'Security on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'security / encryption '
                                                      'tasks.']},
    'pyobjc-framework-securityfoundation': {   'category': 'Security / '
                                                           'Encryption',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'SecurityFoundation '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'security / '
                                                                'encryption '
                                                                'tasks.']},
    'pyobjc-framework-securityinterface': {   'category': 'Security / '
                                                          'Encryption',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'SecurityInterface on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'security / '
                                                               'encryption '
                                                               'tasks.']},
    'pyobjc-framework-securityui': {   'category': 'Security / Encryption',
                                       'purpose': 'Wrappers for the framework '
                                                  'SecurityUI on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'security / encryption '
                                                        'tasks.']},
    'pyobjc-framework-sensitivecontentanalysis': {   'category': 'Unknown / '
                                                                 'General',
                                                     'purpose': 'Wrappers for '
                                                                'the framework '
                                                                'SensitiveContentAnalysis '
                                                                'on macOS',
                                                     'use_cases': [   'Potentially '
                                                                      'used '
                                                                      'for '
                                                                      'unknown '
                                                                      '/ '
                                                                      'general '
                                                                      'tasks.']},
    'pyobjc-framework-servicemanagement': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ServiceManagement on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-sharedwithyou': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework SharedWithYou '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-sharedwithyoucore': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'SharedWithYouCore on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-shazamkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ShazamKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-social': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Social on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-soundanalysis': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework SoundAnalysis '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-speech': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Speech on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-spritekit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SpriteKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-storekit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'StoreKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-symbols': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'Symbols on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-syncservices': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework SyncServices on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-systemconfiguration': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'SystemConfiguration '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-systemextensions': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'SystemExtensions on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-threadnetwork': {   'category': 'Networking',
                                          'purpose': 'Wrappers for the '
                                                     'framework ThreadNetwork '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for networking '
                                                           'tasks.']},
    'pyobjc-framework-uniformtypeidentifiers': {   'category': 'Database / '
                                                               'Storage',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'UniformTypeIdentifiers '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'database '
                                                                    '/ storage '
                                                                    'tasks.']},
    'pyobjc-framework-usernotifications': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'UserNotifications on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-usernotificationsui': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'UserNotificationsUI '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-videosubscriberaccount': {   'category': 'Unknown / '
                                                               'General',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'VideoSubscriberAccount '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'unknown / '
                                                                    'general '
                                                                    'tasks.']},
    'pyobjc-framework-videotoolbox': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework VideoToolbox on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-virtualization': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'Virtualization on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-vision': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Vision on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-webkit': {   'category': 'Web Framework',
                                   'purpose': 'Wrappers for the framework '
                                              'WebKit on macOS',
                                   'use_cases': [   'Potentially used for web '
                                                    'framework tasks.']},
    'pyopengl': {   'category': 'Visualization',
                    'purpose': 'Standard OpenGL bindings for Python',
                    'use_cases': ['Potentially used for visualization tasks.']},
    'pyparsing': {   'category': 'Unknown / General',
                     'purpose': 'pyparsing module - Classes and methods to '
                                'define and execute parsing grammars',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pypdf': {   'category': 'Database / Storage',
                 'purpose': 'A pure-python PDF library capable of splitting, '
                            'merging, cropping, and transforming PDF files',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'pypdfium2': {   'category': 'Unknown / General',
                     'purpose': 'Python bindings to PDFium',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pyperclip': {   'category': 'Machine Learning',
                     'purpose': 'A cross-platform clipboard module for Python. '
                                '(Only handles plain text for now.)',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pypika': {   'category': 'Data Analysis',
                  'purpose': 'A SQL query builder API for Python',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'pyproject_hooks': {   'category': 'Machine Learning',
                           'purpose': 'Wrappers to call pyproject.toml-based '
                                      'build backend hooks.',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'pyqt6': {   'category': 'Database / Storage',
                 'purpose': 'Python bindings for the Qt cross platform '
                            'application toolkit',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'pyqt6-qt6': {   'category': 'Unknown / General',
                     'purpose': 'The subset of a Qt installation needed by '
                                'PyQt6.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pyqt6_sip': {   'category': 'Unknown / General',
                     'purpose': 'The sip module support for PyQt6',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pyro-api': {   'category': 'Web Framework',
                    'purpose': 'Generic API for dispatch to Pyro backends.',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'pyro-ppl': {   'category': 'Machine Learning',
                    'purpose': 'A Python library for probabilistic modeling '
                               'and inference',
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'pyserial': {   'category': 'Unknown / General',
                    'purpose': 'Python Serial Port Extension',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pysocks': {   'category': 'Database / Storage',
                   'purpose': 'A Python SOCKS client module. See '
                              'https://github.com/Anorov/PySocks for more '
                              'information.',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'pytensor': {   'category': 'Unknown / General',
                    'purpose': 'Optimizing compiler for evaluating '
                               'mathematical expressions on CPUs and GPUs.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pytest': {   'category': 'Unknown / General',
                  'purpose': 'pytest: simple powerful testing with Python',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'python-bidi': {   'category': 'Unknown / General',
                       'purpose': 'Python Bidi layout wrapping the Rust crate '
                                  'unicode-bidi',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'python-dateutil': {   'category': 'Unknown / General',
                           'purpose': 'Extensions to the standard Python '
                                      'datetime module',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'python-dotenv': {   'category': 'Machine Learning',
                         'purpose': 'Read key-value pairs from a .env file and '
                                    'set them as environment variables',
                         'use_cases': [   'Potentially used for machine '
                                          'learning tasks.']},
    'python-engineio': {   'category': 'Unknown / General',
                           'purpose': 'Engine.IO server and client for Python',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'python-gitlab': {   'category': 'Web Framework',
                         'purpose': 'The python wrapper for the GitLab REST '
                                    'and GraphQL APIs.',
                         'use_cases': [   'Potentially used for web framework '
                                          'tasks.']},
    'python-json-logger': {   'category': 'Database / Storage',
                              'purpose': 'JSON Log Formatter for the Python '
                                         'Logging Package',
                              'use_cases': [   'Potentially used for database '
                                               '/ storage tasks.']},
    'python-multipart': {   'category': 'Unknown / General',
                            'purpose': 'A streaming multipart parser for '
                                       'Python',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'python-socketio': {   'category': 'Networking',
                           'purpose': 'Socket.IO server and client for Python',
                           'use_cases': [   'Potentially used for networking '
                                            'tasks.']},
    'python-vlc': {   'category': 'Unknown / General',
                      'purpose': 'VLC bindings for python.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'pythonanddragons': {   'category': 'Unknown / General',
                            'purpose': 'DND functions in python!',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'pytoolconfig': {   'category': 'Unknown / General',
                        'purpose': 'Python tool configuration',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'pytorchcv': {   'category': 'Machine Learning',
                     'purpose': 'Computer vision models for PyTorch',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pyttsx3': {   'category': 'Web Framework',
                   'purpose': 'Text to Speech (TTS) library for Python 3. '
                              'Works without internet connection or delay. '
                              'Supports multiple TTS engines, including Sapi5, '
                              'nsss, and espeak.',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'pytz': {   'category': 'Unknown / General',
                'purpose': 'World timezone definitions, modern and historical',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'pyvis': {   'category': 'Visualization',
                 'purpose': 'A Python network graph visualization library',
                 'use_cases': ['Potentially used for visualization tasks.']},
    'pywavelets': {   'category': 'Database / Storage',
                      'purpose': 'PyWavelets, wavelet transform module',
                      'use_cases': [   'Potentially used for database / '
                                       'storage tasks.']},
    'pyyaml': {   'category': 'Machine Learning',
                  'purpose': 'YAML parser and emitter for Python',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'pyzmq': {   'category': 'Unknown / General',
                 'purpose': 'Python bindings for 0MQ',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'qpalm': {   'category': 'Unknown / General',
                 'purpose': 'Proximal Augmented Lagrangian method for '
                            'Quadratic Programs',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'qpax': {   'category': 'Unknown / General',
                'purpose': 'Differentiable QP solver in JAX.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'qpsolvers': {   'category': 'Web Framework',
                     'purpose': 'Quadratic programming solvers in Python with '
                                'a unified API.',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'quadprog': {   'category': 'Unknown / General',
                    'purpose': 'Quadratic Programming Solver',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'questplus': {   'category': 'Machine Learning',
                     'purpose': 'A QUEST+ implementation in Python.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'rdflib': {   'category': 'Database / Storage',
                  'purpose': 'RDFLib is a Python library for working with RDF, '
                             'a simple yet powerful language for representing '
                             'information.',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'readchar': {   'category': 'Unknown / General',
                    'purpose': 'Library to easily read single chars and key '
                               'strokes',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'redbaron': {   'category': 'Unknown / General',
                    'purpose': 'Abstraction on top of baron, a FST for python '
                               'to make writing refactoring code a realistic '
                               'task',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'redis': {   'category': 'Data Analysis',
                 'purpose': 'Python client for Redis database and key-value '
                            'store',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'referencing': {   'category': 'Web Framework',
                       'purpose': 'JSON Referencing + Python',
                       'use_cases': [   'Potentially used for web framework '
                                        'tasks.']},
    'regex': {   'category': 'Unknown / General',
                 'purpose': 'Alternative regular expression module, to replace '
                            're.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'requests': {   'category': 'Networking',
                    'purpose': 'Python HTTP for Humans.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'requests-oauthlib': {   'category': 'Networking',
                             'purpose': 'OAuthlib authentication support for '
                                        'Requests.',
                             'use_cases': [   'Potentially used for networking '
                                              'tasks.']},
    'requests-toolbelt': {   'category': 'Networking',
                             'purpose': 'A utility belt for advanced users of '
                                        'python-requests',
                             'use_cases': [   'Potentially used for networking '
                                              'tasks.']},
    'rfc3339-validator': {   'category': 'Unknown / General',
                             'purpose': 'A pure python RFC3339 validator',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'rfc3986-validator': {   'category': 'Unknown / General',
                             'purpose': 'Pure python rfc3986 validator',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'rfc3987-syntax': {   'category': 'Unknown / General',
                          'purpose': 'Helper functions to syntactically '
                                     'validate strings according to RFC 3987.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'rich': {   'category': 'Unknown / General',
                'purpose': 'Render rich text, tables, progress bars, syntax '
                           'highlighting, markdown and more to the terminal',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'river': {   'category': 'Unknown / General',
                 'purpose': 'Online machine learning in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'rope': {   'category': 'Unknown / General',
                'purpose': 'a python refactoring library...',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'rpds-py': {   'category': 'Data Analysis',
                   'purpose': "Python bindings to Rust's persistent data "
                              'structures (rpds)',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'rply': {   'category': 'Unknown / General',
                'purpose': 'A pure Python Lex/Yacc that works with RPython',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'rsa': {   'category': 'Unknown / General',
               'purpose': 'Pure-Python RSA implementation',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'ruamel.yaml': {   'category': 'Machine Learning',
                       'purpose': 'ruamel.yaml is a YAML parser/emitter that '
                                  'supports roundtrip preservation of '
                                  'comments, seq/map flow style, and map key '
                                  'order',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'ruamel.yaml.clib': {   'category': 'Machine Learning',
                            'purpose': 'C version of reader, parser and '
                                       'emitter for ruamel.yaml derived from '
                                       'libyaml',
                            'use_cases': [   'Potentially used for machine '
                                             'learning tasks.']},
    'ruff': {   'category': 'Database / Storage',
                'purpose': 'An extremely fast Python linter and code '
                           'formatter, written in Rust.',
                'use_cases': [   'Potentially used for database / storage '
                                 'tasks.']},
    'runs': {   'category': 'Unknown / General',
                'purpose': '🏃 Run a block of text as a subprocess 🏃',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'safehttpx': {   'category': 'Unknown / General',
                     'purpose': 'A small Python library created to help '
                                'developers protect their applications from '
                                'Server Side Request Forgery (SSRF) attacks.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'safetensors': {   'category': 'Unknown / General',
                       'purpose': 'Auto-discovered Python library named '
                                  "'safetensors'. Purpose not yet documented.",
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'schedule': {   'category': 'Unknown / General',
                    'purpose': 'Job scheduling for humans.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'scikit-learn': {   'category': 'Data Analysis',
                        'purpose': 'A set of python modules for machine '
                                   'learning and data mining',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'scipy': {   'category': 'Unknown / General',
                 'purpose': 'Fundamental algorithms for scientific computing '
                            'in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'scs': {   'category': 'Unknown / General',
               'purpose': 'Splitting conic solver',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'selenium': {   'category': 'Web Framework',
                    'purpose': 'Official Python bindings for Selenium '
                               'WebDriver',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'semantic-version': {   'category': 'Unknown / General',
                            'purpose': "A library implementing the 'SemVer' "
                                       'scheme.',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'send2trash': {   'category': 'Unknown / General',
                      'purpose': 'Send file to trash natively under Mac OS X, '
                                 'Windows and Linux',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'sentence-transformers': {   'category': 'Machine Learning',
                                 'purpose': 'Embeddings, Retrieval, and '
                                            'Reranking',
                                 'use_cases': [   'Potentially used for '
                                                  'machine learning tasks.']},
    'sentencepiece': {   'category': 'Unknown / General',
                         'purpose': 'Unsupervised text tokenizer and '
                                    'detokenizer.',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'sentry-sdk': {   'category': 'Networking',
                      'purpose': 'Python client for Sentry (https://sentry.io)',
                      'use_cases': ['Potentially used for networking tasks.']},
    'setuptools': {   'category': 'Unknown / General',
                      'purpose': 'Easily download, build, install, upgrade, '
                                 'and uninstall Python packages',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'sgmllib3k': {   'category': 'Machine Learning',
                     'purpose': 'Py3k port of sgmllib.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'shellingham': {   'category': 'Unknown / General',
                       'purpose': 'Tool to Detect Surrounding Shell',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'shortuuid': {   'category': 'Unknown / General',
                     'purpose': 'A generator library for concise, unambiguous '
                                'and URL-safe UUIDs.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'simple-websocket': {   'category': 'Web Framework',
                            'purpose': 'Simple WebSocket server and client for '
                                       'Python',
                            'use_cases': [   'Potentially used for web '
                                             'framework tasks.']},
    'simpy': {   'category': 'Unknown / General',
                 'purpose': 'Event discrete, process based simulation for '
                            'Python.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'sip_python': {   'category': 'Unknown / General',
                      'purpose': 'Python bindings for the SIP solver.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'six': {   'category': 'Unknown / General',
               'purpose': 'Python 2 and 3 compatibility utilities',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'skl2onnx': {   'category': 'Unknown / General',
                    'purpose': 'Convert scikit-learn models to ONNX',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'smart_open': {   'category': 'Unknown / General',
                      'purpose': 'Utils for streaming large files (S3, HDFS, '
                                 'GCS, SFTP, Azure Blob Storage, gzip, bz2, '
                                 'zst...)',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'smmap': {   'category': 'Unknown / General',
                 'purpose': 'A pure Python implementation of a sliding window '
                            'memory map manager',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'sniffio': {   'category': 'Networking',
                   'purpose': 'Sniff out which async library your code is '
                              'running under',
                   'use_cases': ['Potentially used for networking tasks.']},
    'sortedcontainers': {   'category': 'Machine Learning',
                            'purpose': 'Sorted Containers -- Sorted List, '
                                       'Sorted Dict, Sorted Set',
                            'use_cases': [   'Potentially used for machine '
                                             'learning tasks.']},
    'sounddevice': {   'category': 'Unknown / General',
                       'purpose': 'Play and Record Sound with Python',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'soundfile': {   'category': 'Unknown / General',
                     'purpose': 'An audio library based on libsndfile, CFFI '
                                'and NumPy',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'soupsieve': {   'category': 'Machine Learning',
                     'purpose': 'A modern CSS selector implementation for '
                                'Beautiful Soup.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'soxr': {   'category': 'Unknown / General',
                'purpose': 'High quality, one-dimensional sample-rate '
                           'conversion library',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'spacy': {   'category': 'Unknown / General',
                 'purpose': 'Industrial-strength Natural Language Processing '
                            '(NLP) in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'spacy-legacy': {   'category': 'Unknown / General',
                        'purpose': 'Legacy registered functions for spaCy '
                                   'backwards compatibility',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'spacy-loggers': {   'category': 'Unknown / General',
                         'purpose': 'Logging utilities for SpaCy',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'speechrecognition': {   'category': 'Web Framework',
                             'purpose': 'Library for performing speech '
                                        'recognition, with support for several '
                                        'engines and APIs, online and offline.',
                             'use_cases': [   'Potentially used for web '
                                              'framework tasks.']},
    'sqlalchemy': {   'category': 'Data Analysis',
                      'purpose': 'Database Abstraction Library',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'sqlmodel': {   'category': 'Data Analysis',
                    'purpose': 'SQLModel, SQL databases in Python, designed '
                               'for simplicity, compatibility, and robustness.',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'srsly': {   'category': 'Database / Storage',
                 'purpose': 'Modern high-performance serialization utilities '
                            'for Python',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'stack-data': {   'category': 'Data Analysis',
                      'purpose': 'Extract data from python stack frames and '
                                 'tracebacks for informative displays',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'starlette': {   'category': 'Unknown / General',
                     'purpose': 'The little ASGI library that shines.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'statsmodels': {   'category': 'Unknown / General',
                       'purpose': 'Statistical computations and models for '
                                  'Python',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'striprtf': {   'category': 'Unknown / General',
                    'purpose': 'A simple library to convert rtf to text',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'sympy': {   'category': 'Unknown / General',
                 'purpose': 'Computer algebra system (CAS) in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'tables': {   'category': 'Data Analysis',
                  'purpose': 'Hierarchical datasets for Python',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'tabulate': {   'category': 'Data Analysis',
                    'purpose': 'Pretty-print tabular data',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'tenacity': {   'category': 'Unknown / General',
                    'purpose': 'Retry code until it succeeds',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'tensorboard': {   'category': 'Machine Learning',
                       'purpose': 'TensorBoard lets you watch Tensors Flow',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'tensorboard-data-server': {   'category': 'Machine Learning',
                                   'purpose': 'Fast data loading for '
                                              'TensorBoard',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'termcolor': {   'category': 'Database / Storage',
                     'purpose': 'ANSI color formatting for output in terminal',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'terminado': {   'category': 'Web Framework',
                     'purpose': 'Tornado websocket backend for the Xterm.js '
                                'Javascript terminal emulator library.',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'textblob': {   'category': 'Unknown / General',
                    'purpose': 'Simple, Pythonic text processing. Sentiment '
                               'analysis, part-of-speech tagging, noun phrase '
                               'parsing, and more.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'thinc': {   'category': 'Machine Learning',
                 'purpose': 'A refreshing functional take on deep learning, '
                            'compatible with your favorite libraries',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'threadpoolctl': {   'category': 'Unknown / General',
                         'purpose': 'threadpoolctl',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'tiktoken': {   'category': 'Machine Learning',
                    'purpose': 'tiktoken is a fast BPE tokeniser for use with '
                               "OpenAI's models",
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'timm': {   'category': 'Machine Learning',
                'purpose': 'PyTorch Image Models',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'tinycss2': {   'category': 'Unknown / General',
                    'purpose': 'A tiny CSS parser',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'tokenizers': {   'category': 'Machine Learning',
                      'purpose': 'Auto-discovered Python library named '
                                 "'tokenizers'. Purpose not yet documented.",
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'tokentrim': {   'category': 'Unknown / General',
                     'purpose': "Easily trim 'messages' arrays for use with "
                                'GPTs.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'toml': {   'category': 'Unknown / General',
                'purpose': "Python Library for Tom's Obvious, Minimal Language",
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'tomli': {   'category': 'Machine Learning',
                 'purpose': "A lil' TOML parser",
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'tomli_w': {   'category': 'Machine Learning',
                   'purpose': "A lil' TOML writer",
                   'use_cases': [   'Potentially used for machine learning '
                                    'tasks.']},
    'tomlkit': {   'category': 'Machine Learning',
                   'purpose': 'Style preserving TOML library',
                   'use_cases': [   'Potentially used for machine learning '
                                    'tasks.']},
    'toolz': {   'category': 'Unknown / General',
                 'purpose': 'List processing tools and functional utilities',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'toposort': {   'category': 'Unknown / General',
                    'purpose': 'Implements a topological sort algorithm.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'torch': {   'category': 'Machine Learning',
                 'purpose': 'Tensors and Dynamic neural networks in Python '
                            'with strong GPU acceleration',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'torchaudio': {   'category': 'Machine Learning',
                      'purpose': 'An audio package for PyTorch',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'torchmetrics': {   'category': 'Machine Learning',
                        'purpose': 'PyTorch native Metrics',
                        'use_cases': [   'Potentially used for machine '
                                         'learning tasks.']},
    'torchvision': {   'category': 'Machine Learning',
                       'purpose': 'image and video datasets and models for '
                                  'torch deep learning',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'tornado': {   'category': 'Web Framework',
                   'purpose': 'Tornado is a Python web framework and '
                              'asynchronous networking library, originally '
                              'developed at FriendFeed.',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'tqdm': {   'category': 'Unknown / General',
                'purpose': 'Fast, Extensible Progress Meter',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'traitlets': {   'category': 'Machine Learning',
                     'purpose': 'Traitlets Python configuration system',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'transformers': {   'category': 'Machine Learning',
                        'purpose': 'State-of-the-art Machine Learning for JAX, '
                                   'PyTorch and TensorFlow',
                        'use_cases': [   'Potentially used for machine '
                                         'learning tasks.']},
    'transitions': {   'category': 'Unknown / General',
                       'purpose': 'A lightweight, object-oriented Python state '
                                  'machine implementation with many '
                                  'extensions.',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'trio': {   'category': 'Networking',
                'purpose': 'A friendly Python library for async concurrency '
                           'and I/O',
                'use_cases': ['Potentially used for networking tasks.']},
    'trio-websocket': {   'category': 'Web Framework',
                          'purpose': 'WebSocket library for Trio',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'truststore': {   'category': 'Unknown / General',
                      'purpose': 'Verify certificates using native system '
                                 'trust stores',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ty': {   'category': 'Unknown / General',
              'purpose': 'An extremely fast Python type checker, written in '
                         'Rust.',
              'use_cases': ['Potentially used for unknown / general tasks.']},
    'typer': {   'category': 'Unknown / General',
                 'purpose': 'Typer, build great CLIs. Easy to code. Based on '
                            'Python type hints.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'typing-inspect': {   'category': 'Unknown / General',
                          'purpose': 'Runtime inspection utilities for typing '
                                     'module.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'typing-inspection': {   'category': 'Unknown / General',
                             'purpose': 'Runtime typing introspection tools',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'typing_extensions': {   'category': 'Unknown / General',
                             'purpose': 'Backported and Experimental Type '
                                        'Hints for Python 3.9+',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'tzdata': {   'category': 'Data Analysis',
                  'purpose': 'Provider of IANA time zone data',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'tzlocal': {   'category': 'Unknown / General',
                   'purpose': 'tzinfo object for the local timezone',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'ujson': {   'category': 'Unknown / General',
                 'purpose': 'Ultra fast JSON encoder and decoder for Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'unicodedata2': {   'category': 'Data Analysis',
                        'purpose': 'Unicodedata backport updated to the latest '
                                   'Unicode version.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'uri-template': {   'category': 'Unknown / General',
                        'purpose': 'RFC 6570 URI Template Processor',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'uritemplate': {   'category': 'Unknown / General',
                       'purpose': 'Implementation of RFC 6570 URI Templates',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'urllib3': {   'category': 'Networking',
                   'purpose': 'HTTP library with thread-safe connection '
                              'pooling, file post, and more.',
                   'use_cases': ['Potentially used for networking tasks.']},
    'uv': {   'category': 'Unknown / General',
              'purpose': 'An extremely fast Python package and project '
                         'manager, written in Rust.',
              'use_cases': ['Potentially used for unknown / general tasks.']},
    'uvicorn': {   'category': 'Unknown / General',
                   'purpose': 'The lightning-fast ASGI server.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'uvloop': {   'category': 'Networking',
                  'purpose': 'Fast implementation of asyncio event loop on top '
                             'of libuv',
                  'use_cases': ['Potentially used for networking tasks.']},
    'vadersentiment': {   'category': 'Machine Learning',
                          'purpose': 'VADER Sentiment Analysis. VADER (Valence '
                                     'Aware Dictionary and sEntiment Reasoner) '
                                     'is a lexicon and rule-based sentiment '
                                     'analysis tool that is specifically '
                                     'attuned to sentiments expressed in '
                                     'social media, and works well on texts '
                                     'from other domains.',
                          'use_cases': [   'Potentially used for machine '
                                           'learning tasks.']},
    'virtualenv': {   'category': 'Unknown / General',
                      'purpose': 'Virtual Python Environment builder',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'wandb': {   'category': 'Web Framework',
                 'purpose': 'A CLI and library for interacting with the '
                            'Weights & Biases API.',
                 'use_cases': ['Potentially used for web framework tasks.']},
    'wasabi': {   'category': 'Database / Storage',
                  'purpose': 'A lightweight console printing and formatting '
                             'toolkit',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'watchdog': {   'category': 'Unknown / General',
                    'purpose': 'Filesystem events monitoring',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'watchfiles': {   'category': 'Database / Storage',
                      'purpose': 'Simple, modern and high performance file '
                                 'watching and code reload in python.',
                      'use_cases': [   'Potentially used for database / '
                                       'storage tasks.']},
    'wcwidth': {   'category': 'Unknown / General',
                   'purpose': 'Measures the displayed width of unicode strings '
                              'in a terminal',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'weasel': {   'category': 'Unknown / General',
                  'purpose': 'Weasel: A small and easy workflow system',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'webcolors': {   'category': 'Machine Learning',
                     'purpose': 'A library for working with the color formats '
                                'defined by HTML and CSS.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'webdriver-manager': {   'category': 'Unknown / General',
                             'purpose': 'Library provides the way to '
                                        'automatically manage drivers for '
                                        'different browsers',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'webencodings': {   'category': 'Web Framework',
                        'purpose': 'Character encoding aliases for legacy web '
                                   'content',
                        'use_cases': [   'Potentially used for web framework '
                                         'tasks.']},
    'websocket-client': {   'category': 'Web Framework',
                            'purpose': 'WebSocket client for Python with low '
                                       'level API options',
                            'use_cases': [   'Potentially used for web '
                                             'framework tasks.']},
    'websockets': {   'category': 'Web Framework',
                      'purpose': 'An implementation of the WebSocket Protocol '
                                 '(RFC 6455 & 7692)',
                      'use_cases': [   'Potentially used for web framework '
                                       'tasks.']},
    'werkzeug': {   'category': 'Web Framework',
                    'purpose': 'The comprehensive WSGI web application '
                               'library.',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'wget': {   'category': 'Unknown / General',
                'purpose': 'pure python download utility',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'wheel': {   'category': 'Database / Storage',
                 'purpose': 'A built-package format for Python',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'widgetsnbextension': {   'category': 'Web Framework',
                              'purpose': 'Jupyter interactive widgets for '
                                         'Jupyter Notebook',
                              'use_cases': [   'Potentially used for web '
                                               'framework tasks.']},
    'wikipedia': {   'category': 'Web Framework',
                     'purpose': 'Wikipedia API for Python',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'wrapt': {   'category': 'Unknown / General',
                 'purpose': 'Module for decorators, wrappers and monkey '
                            'patching.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'wsproto': {   'category': 'Web Framework',
                   'purpose': 'WebSockets state-machine based protocol '
                              'implementation',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'wxpython': {   'category': 'Database / Storage',
                    'purpose': 'Cross platform GUI toolkit for Python, '
                               '"Phoenix" version',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'xarray': {   'category': 'Data Analysis',
                  'purpose': 'N-D labeled arrays and datasets in Python',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'xarray-einstats': {   'category': 'Unknown / General',
                           'purpose': 'Stats, linear algebra and einops for '
                                      'xarray',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'xmlschema': {   'category': 'Machine Learning',
                     'purpose': 'An XML Schema validator and decoder',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'xmod': {   'category': 'Unknown / General',
                'purpose': '🌱 Turn any object into a module 🌱',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'xxhash': {   'category': 'Unknown / General',
                  'purpose': 'Python binding for xxHash',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'xyzservices': {   'category': 'Unknown / General',
                       'purpose': 'Source of XYZ tiles providers',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'yarl': {   'category': 'Unknown / General',
                'purpose': 'Yet another URL library',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'yaspin': {   'category': 'Unknown / General',
                  'purpose': 'Yet Another Terminal Spinner',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'zeroconf': {   'category': 'Unknown / General',
                    'purpose': 'A pure python implementation of multicast DNS '
                               'service discovery',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'zipp': {   'category': 'Unknown / General',
                'purpose': 'Backport of pathlib-compatible object wrapper for '
                           'zip files',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'zope.event': {   'category': 'Unknown / General',
                      'purpose': 'Very basic event publishing system',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'zope.interface': {   'category': 'Unknown / General',
                          'purpose': 'Interfaces for Python',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'zstandard': {   'category': 'Unknown / General',
                     'purpose': 'Zstandard bindings for Python',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']}}
,
    'accelerate': {   'category': 'Machine Learning',
                      'purpose': 'Accelerate',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'aiofiles': {   'category': 'Networking',
                    'purpose': 'File support for asyncio.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'aiohappyeyeballs': {   'category': 'Networking',
                            'purpose': 'Happy Eyeballs for asyncio',
                            'use_cases': [   'Potentially used for networking '
                                             'tasks.']},
    'aiohttp': {   'category': 'Networking',
                   'purpose': 'Async http client/server framework (asyncio)',
                   'use_cases': ['Potentially used for networking tasks.']},
    'aiosignal': {   'category': 'Machine Learning',
                     'purpose': 'aiosignal: a list of registered asynchronous '
                                'callbacks',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'aiosqlite': {   'category': 'Database / Storage',
                     'purpose': 'asyncio bridge to the standard sqlite3 module',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'alembic': {   'category': 'Data Analysis',
                   'purpose': 'A database migration tool for SQLAlchemy.',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'annotated-types': {   'category': 'Machine Learning',
                           'purpose': 'Reusable constraint types to use with '
                                      'typing.Annotated',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'anthropic': {   'category': 'Web Framework',
                     'purpose': 'The official Python library for the anthropic '
                                'API',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'anyio': {   'category': 'Networking',
                 'purpose': 'High-level concurrency and networking framework '
                            'on top of asyncio or Trio',
                 'use_cases': ['Potentially used for networking tasks.']},
    'appdirs': {   'category': 'Data Analysis',
                   'purpose': 'A small Python module for determining '
                              'appropriate platform-specific dirs, e.g. a '
                              '"user data dir".',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'appnope': {   'category': 'Unknown / General',
                   'purpose': 'Disable App Nap on macOS >= 10.9',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'apricot-select': {   'category': 'Unknown / General',
                          'purpose': 'apricot is a package for submodular '
                                     'selection of representative sets for '
                                     'machine learning models.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'apscheduler': {   'category': 'Unknown / General',
                       'purpose': 'In-process task scheduler with Cron-like '
                                  'capabilities',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'archspec': {   'category': 'Unknown / General',
                    'purpose': 'A library to query system architecture',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'astor': {   'category': 'Unknown / General',
                 'purpose': 'Read/rewrite/write Python ASTs',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'asttokens': {   'category': 'Unknown / General',
                     'purpose': 'Annotate AST trees with source code positions',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'attrs': {   'category': 'Unknown / General',
                 'purpose': 'Classes Without Boilerplate',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'autogen-agentchat': {   'category': 'Unknown / General',
                             'purpose': 'AutoGen agents and teams library',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'autogen-core': {   'category': 'Unknown / General',
                        'purpose': 'Foundational interfaces and agent runtime '
                                   'implementation for AutoGen',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'avalanche-lib': {   'category': 'Unknown / General',
                         'purpose': 'Avalanche: a Comprehensive Framework for '
                                    'Continual Learning Research',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'backcall': {   'category': 'Web Framework',
                    'purpose': 'Specifications for callback functions passed '
                               'in to an API',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'backoff': {   'category': 'Unknown / General',
                   'purpose': 'Function decoration for backoff and retry',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'banks': {   'category': 'Unknown / General',
                 'purpose': 'A prompt programming language',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'baron': {   'category': 'Unknown / General',
                 'purpose': 'Full Syntax Tree for python to make writing '
                            'refactoring code a realist task',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'bcrypt': {   'category': 'Unknown / General',
                  'purpose': 'Modern password hashing for your software and '
                             'your servers',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'beautifulsoup4': {   'category': 'Machine Learning',
                          'purpose': 'Screen-scraping library',
                          'use_cases': [   'Potentially used for machine '
                                           'learning tasks.']},
    'bible': {   'category': 'Machine Learning',
                 'purpose': 'Bible reference classes',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'bidict': {   'category': 'Unknown / General',
                  'purpose': 'The bidirectional mapping library for Python.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'blessed': {   'category': 'Database / Storage',
                   'purpose': 'Easy, practical library for making terminal '
                              'apps, by providing an elegant, well-documented '
                              'interface to Colors, Keyboard input, and screen '
                              'Positioning capabilities.',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'blinker': {   'category': 'Unknown / General',
                   'purpose': 'Fast, simple object-to-object and broadcast '
                              'signaling',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'blis': {   'category': 'Machine Learning',
                'purpose': 'The Blis BLAS-like linear algebra library, as a '
                           'self-contained C-extension.',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'boltons': {   'category': 'Unknown / General',
                   'purpose': "When they're not builtins, they're boltons.",
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'brotli': {   'category': 'Unknown / General',
                  'purpose': 'Python bindings for the Brotli compression '
                             'library',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'build': {   'category': 'Unknown / General',
                 'purpose': 'A simple, correct Python build frontend',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'cachetools': {   'category': 'Unknown / General',
                      'purpose': 'Extensible memoizing collections and '
                                 'decorators',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'catalogue': {   'category': 'Unknown / General',
                     'purpose': 'Super lightweight function registries for '
                                'your library',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'certifi': {   'category': 'Unknown / General',
                   'purpose': "Python package for providing Mozilla's CA "
                              'Bundle.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'cffi': {   'category': 'Unknown / General',
                'purpose': 'Foreign Function Interface for Python calling C '
                           'code.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'charset-normalizer': {   'category': 'Machine Learning',
                              'purpose': 'The Real First Universal Charset '
                                         'Detector. Open, modern and actively '
                                         'maintained alternative to Chardet.',
                              'use_cases': [   'Potentially used for machine '
                                               'learning tasks.']},
    'chromadb': {   'category': 'Unknown / General',
                    'purpose': 'Chroma.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'clarabel': {   'category': 'Unknown / General',
                    'purpose': 'Clarabel Conic Interior Point Solver for Rust '
                               '/ Python',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'click': {   'category': 'Unknown / General',
                 'purpose': 'Composable command line interface toolkit',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'cloudpathlib': {   'category': 'Unknown / General',
                        'purpose': 'pathlib-style classes for cloud storage '
                                   'services.',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'cmeel': {   'category': 'Unknown / General',
                 'purpose': 'Create Wheel from CMake projects',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'colorama': {   'category': 'Database / Storage',
                    'purpose': 'Cross-platform colored terminal text.',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'coloredlogs': {   'category': 'Unknown / General',
                       'purpose': "Colored terminal output for Python's "
                                  'logging module',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'colorlog': {   'category': 'Unknown / General',
                    'purpose': "Add colours to the output of Python's logging "
                               'module.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'comm': {   'category': 'Unknown / General',
                'purpose': 'Jupyter Python Comm implementation, for usage in '
                           'ipykernel, xeus-python etc.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'confection': {   'category': 'Unknown / General',
                      'purpose': 'The sweetest config system for Python',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'contourpy': {   'category': 'Unknown / General',
                     'purpose': 'Python library for calculating contours of 2D '
                                'quadrilateral grids',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'cvxopt': {   'category': 'Unknown / General',
                  'purpose': 'Convex optimization package',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'cycler': {   'category': 'Unknown / General',
                  'purpose': 'Composable style cycles',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'cymem': {   'category': 'Unknown / General',
                 'purpose': 'Manage calls to calloc/free through Cython',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'daqp': {   'category': 'Unknown / General',
                'purpose': 'DAQP: A dual active-set QP solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'dataclasses-json': {   'category': 'Data Analysis',
                            'purpose': 'Easily serialize dataclasses to and '
                                       'from JSON.',
                            'use_cases': [   'Potentially used for data '
                                             'analysis tasks.']},
    'debugpy': {   'category': 'Unknown / General',
                   'purpose': 'An implementation of the Debug Adapter Protocol '
                              'for Python',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'decorator': {   'category': 'Unknown / General',
                     'purpose': 'Decorators for Humans',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'defusedxml': {   'category': 'Machine Learning',
                      'purpose': 'XML bomb protection for Python stdlib '
                                 'modules',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'deprecated': {   'category': 'Unknown / General',
                      'purpose': 'Python @deprecated decorator to deprecate '
                                 'old python classes, functions or methods.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'dill': {   'category': 'Unknown / General',
                'purpose': 'serialize all of Python',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'dirtyjson': {   'category': 'Data Analysis',
                     'purpose': 'JSON decoder for Python that can extract data '
                                'from the muck',
                     'use_cases': [   'Potentially used for data analysis '
                                      'tasks.']},
    'diskcache': {   'category': 'Unknown / General',
                     'purpose': 'Disk Cache -- Disk and file backed persistent '
                                'cache.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'distro': {   'category': 'Web Framework',
                  'purpose': 'Distro - an OS platform information API',
                  'use_cases': ['Potentially used for web framework tasks.']},
    'durationpy': {   'category': 'Unknown / General',
                      'purpose': 'Module for converting between '
                                 "datetime.timedelta and Go's Duration "
                                 'strings.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ecos': {   'category': 'Database / Storage',
                'purpose': 'This is the Python package for ECOS: Embedded Cone '
                           'Solver. See Github page for more information.',
                'use_cases': [   'Potentially used for database / storage '
                                 'tasks.']},
    'editor': {   'category': 'Unknown / General',
                  'purpose': '🖋 Open the default text editor 🖋',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'en_core_web_sm': {   'category': 'Unknown / General',
                          'purpose': 'English pipeline optimized for CPU. '
                                     'Components: tok2vec, tagger, parser, '
                                     'senter, ner, attribute_ruler, '
                                     'lemmatizer.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'executing': {   'category': 'Database / Storage',
                     'purpose': 'Get the currently executing AST node of a '
                                'frame, and other information',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'faiss-cpu': {   'category': 'Machine Learning',
                     'purpose': 'A library for efficient similarity search and '
                                'clustering of dense vectors.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'fastapi': {   'category': 'Web Framework',
                   'purpose': 'FastAPI framework, high performance, easy to '
                              'learn, fast to code, ready for production',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'fastuuid': {   'category': 'Unknown / General',
                    'purpose': "Python bindings to Rust's UUID library.",
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'feedparser': {   'category': 'Unknown / General',
                      'purpose': 'Universal feed parser, handles RSS 0.9x, RSS '
                                 '1.0, RSS 2.0, CDF, Atom 0.3, and Atom 1.0 '
                                 'feeds',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'ffmpy': {   'category': 'Unknown / General',
                 'purpose': 'A simple Python wrapper for FFmpeg',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'filelock': {   'category': 'Database / Storage',
                    'purpose': 'A platform independent file lock.',
                    'use_cases': [   'Potentially used for database / storage '
                                     'tasks.']},
    'filetype': {   'category': 'Unknown / General',
                    'purpose': 'Infer file type and MIME type of any '
                               'file/buffer. No external dependencies.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'flask': {   'category': 'Web Framework',
                 'purpose': 'A simple framework for building complex web '
                            'applications.',
                 'use_cases': ['Potentially used for web framework tasks.']},
    'flask-socketio': {   'category': 'Web Framework',
                          'purpose': 'Socket.IO integration for Flask '
                                     'applications',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'flatbuffers': {   'category': 'Database / Storage',
                       'purpose': 'The FlatBuffers serialization format for '
                                  'Python',
                       'use_cases': [   'Potentially used for database / '
                                        'storage tasks.']},
    'fonttools': {   'category': 'Unknown / General',
                     'purpose': 'Tools to manipulate font files',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'frozendict': {   'category': 'Unknown / General',
                      'purpose': 'A simple immutable dictionary',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'frozenlist': {   'category': 'Unknown / General',
                      'purpose': 'A list-like structure which implements '
                                 'collections.abc.MutableSequence',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'fsspec': {   'category': 'Unknown / General',
                  'purpose': 'File-system specification',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'gdown': {   'category': 'Unknown / General',
                 'purpose': 'Google Drive Public File/Folder Downloader',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'git-python': {   'category': 'Unknown / General',
                      'purpose': 'combination and simplification of some '
                                 'useful git commands',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'gitdb': {   'category': 'Data Analysis',
                 'purpose': 'Git Object Database',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'gitpython': {   'category': 'Unknown / General',
                     'purpose': 'GitPython is a Python library used to '
                                'interact with Git repositories',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'gmpy2': {   'category': 'Unknown / General',
                 'purpose': 'gmpy2 interface to GMP, MPFR, and MPC for Python '
                            '3.7+',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'google-ai-generativelanguage': {   'category': 'Machine Learning',
                                        'purpose': 'Google Ai '
                                                   'Generativelanguage API '
                                                   'client library',
                                        'use_cases': [   'Potentially used for '
                                                         'machine learning '
                                                         'tasks.']},
    'google-api-core': {   'category': 'Web Framework',
                           'purpose': 'Google API client core library',
                           'use_cases': [   'Potentially used for web '
                                            'framework tasks.']},
    'google-api-python-client': {   'category': 'Web Framework',
                                    'purpose': 'Google API Client Library for '
                                               'Python',
                                    'use_cases': [   'Potentially used for web '
                                                     'framework tasks.']},
    'google-auth': {   'category': 'Security / Encryption',
                       'purpose': 'Google Authentication Library',
                       'use_cases': [   'Potentially used for security / '
                                        'encryption tasks.']},
    'google-auth-httplib2': {   'category': 'Networking',
                                'purpose': 'Google Authentication Library: '
                                           'httplib2 transport',
                                'use_cases': [   'Potentially used for '
                                                 'networking tasks.']},
    'google-generativeai': {   'category': 'Machine Learning',
                               'purpose': 'Google Generative AI High level API '
                                          'client library and tools.',
                               'use_cases': [   'Potentially used for machine '
                                                'learning tasks.']},
    'googleapis-common-protos': {   'category': 'Web Framework',
                                    'purpose': 'Common protobufs used in '
                                               'Google APIs',
                                    'use_cases': [   'Potentially used for web '
                                                     'framework tasks.']},
    'gputil': {   'category': 'Machine Learning',
                  'purpose': 'GPUtil is a Python module for getting the GPU '
                             'status from NVIDA GPUs using nvidia-smi.',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'gradio': {   'category': 'Machine Learning',
                  'purpose': 'Python library for easily interacting with '
                             'trained machine learning models',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'gradio_client': {   'category': 'Machine Learning',
                         'purpose': 'Python library for easily interacting '
                                    'with trained machine learning models',
                         'use_cases': [   'Potentially used for machine '
                                          'learning tasks.']},
    'graphviz': {   'category': 'Visualization',
                    'purpose': 'Simple Python interface for Graphviz',
                    'use_cases': ['Potentially used for visualization tasks.']},
    'greenlet': {   'category': 'Unknown / General',
                    'purpose': 'Lightweight in-process concurrent programming',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'griffe': {   'category': 'Web Framework',
                  'purpose': 'Signatures for entire Python programs. Extract '
                             'the structure, the frame, the skeleton of your '
                             'project, to generate API documentation or find '
                             'breaking changes in your API.',
                  'use_cases': ['Potentially used for web framework tasks.']},
    'groovy': {   'category': 'Unknown / General',
                  'purpose': 'A small Python library created to help '
                             'developers protect their applications from '
                             'Server Side Request Forgery (SSRF) attacks.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'grpcio': {   'category': 'Networking',
                  'purpose': 'HTTP/2-based RPC framework',
                  'use_cases': ['Potentially used for networking tasks.']},
    'grpcio-status': {   'category': 'Unknown / General',
                         'purpose': 'Status proto mapping for gRPC',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'gunicorn': {   'category': 'Networking',
                    'purpose': 'WSGI HTTP Server for UNIX',
                    'use_cases': ['Potentially used for networking tasks.']},
    'h11': {   'category': 'Networking',
               'purpose': 'A pure-Python, bring-your-own-I/O implementation of '
                          'HTTP/1.1',
               'use_cases': ['Potentially used for networking tasks.']},
    'h2': {   'category': 'Networking',
              'purpose': 'Pure-Python HTTP/2 protocol implementation',
              'use_cases': ['Potentially used for networking tasks.']},
    'hf-xet': {   'category': 'Unknown / General',
                  'purpose': 'Fast transfer of large files with the Hugging '
                             'Face Hub.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'highspy': {   'category': 'Unknown / General',
                   'purpose': 'A thin set of pybind11 wrappers to HiGHS',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'hpack': {   'category': 'Unknown / General',
                 'purpose': 'Pure-Python HPACK header encoding',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'html2image': {   'category': 'Machine Learning',
                      'purpose': 'Package acting as a wrapper around the '
                                 'headless mode of existing web browsers to '
                                 'generate images from URLs and from HTML+CSS '
                                 'strings or files.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'html2text': {   'category': 'Machine Learning',
                     'purpose': 'Turn HTML into equivalent Markdown-structured '
                                'text.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'httpcore': {   'category': 'Networking',
                    'purpose': 'A minimal low-level HTTP client.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'httplib2': {   'category': 'Networking',
                    'purpose': 'A comprehensive HTTP client library.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'httptools': {   'category': 'Networking',
                     'purpose': 'A collection of framework independent HTTP '
                                'protocol utils.',
                     'use_cases': ['Potentially used for networking tasks.']},
    'httpx': {   'category': 'Networking',
                 'purpose': 'The next generation HTTP client.',
                 'use_cases': ['Potentially used for networking tasks.']},
    'huggingface-hub': {   'category': 'Machine Learning',
                           'purpose': 'Client library to download and publish '
                                      'models, datasets and other repos on the '
                                      'huggingface.co hub',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'humanfriendly': {   'category': 'Unknown / General',
                         'purpose': 'Human friendly output for text interfaces '
                                    'using Python',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'hyperframe': {   'category': 'Networking',
                      'purpose': 'Pure-Python HTTP/2 framing',
                      'use_cases': ['Potentially used for networking tasks.']},
    'idna': {   'category': 'Machine Learning',
                'purpose': 'Internationalized Domain Names in Applications '
                           '(IDNA)',
                'use_cases': ['Potentially used for machine learning tasks.']},
    'importlib_metadata': {   'category': 'Data Analysis',
                              'purpose': 'Read metadata from Python packages',
                              'use_cases': [   'Potentially used for data '
                                               'analysis tasks.']},
    'importlib_resources': {   'category': 'Unknown / General',
                               'purpose': 'Read resources from Python packages',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'iniconfig': {   'category': 'Machine Learning',
                     'purpose': 'brain-dead simple config-ini parsing',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'inquirer': {   'category': 'Unknown / General',
                    'purpose': 'Collection of common interactive command line '
                               'user interfaces, based on Inquirer.js',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'ipykernel': {   'category': 'Web Framework',
                     'purpose': 'IPython Kernel for Jupyter',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'ipython': {   'category': 'Unknown / General',
                   'purpose': 'IPython: Productive Interactive Computing',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'ipython_pygments_lexers': {   'category': 'Unknown / General',
                                   'purpose': 'Defines a variety of Pygments '
                                              'lexers for highlighting IPython '
                                              'code.',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'itsdangerous': {   'category': 'Data Analysis',
                        'purpose': 'Safely pass data to untrusted environments '
                                   'and back.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'jax': {   'category': 'Database / Storage',
               'purpose': 'Differentiate, compile, and transform Numpy code.',
               'use_cases': ['Potentially used for database / storage tasks.']},
    'jaxlib': {   'category': 'Unknown / General',
                  'purpose': 'XLA library for JAX',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jaxopt': {   'category': 'Unknown / General',
                  'purpose': 'Hardware accelerated, batchable and '
                             'differentiable optimizers in JAX.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jedi': {   'category': 'Unknown / General',
                'purpose': 'An autocompletion tool for Python that can be used '
                           'for text editors.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'jinja2': {   'category': 'Unknown / General',
                  'purpose': 'A very fast and expressive template engine.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jiter': {   'category': 'Unknown / General',
                 'purpose': 'Fast iterable JSON parser.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'joblib': {   'category': 'Unknown / General',
                  'purpose': 'Lightweight pipelining with Python functions',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'jsonpatch': {   'category': 'Unknown / General',
                     'purpose': 'Apply JSON-Patches (RFC 6902)',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'jsonpointer': {   'category': 'Unknown / General',
                       'purpose': 'Identify specific nodes in a JSON document '
                                  '(RFC 6901)',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'jsonref': {   'category': 'Unknown / General',
                   'purpose': 'jsonref is a library for automatic '
                              'dereferencing of JSON Reference objects for '
                              'Python.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'jsonschema': {   'category': 'Data Analysis',
                      'purpose': 'An implementation of JSON Schema validation '
                                 'for Python',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'jsonschema-specifications': {   'category': 'Data Analysis',
                                     'purpose': 'The JSON Schema meta-schemas '
                                                'and vocabularies, exposed as '
                                                'a Registry',
                                     'use_cases': [   'Potentially used for '
                                                      'data analysis tasks.']},
    'jupyter_client': {   'category': 'Web Framework',
                          'purpose': 'Jupyter protocol implementation and '
                                     'client libraries',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'jupyter_core': {   'category': 'Unknown / General',
                        'purpose': 'Jupyter core package. A base package on '
                                   'which Jupyter projects rely.',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'kiwisolver': {   'category': 'Machine Learning',
                      'purpose': 'A fast implementation of the Cassowary '
                                 'constraint solver',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'kubernetes': {   'category': 'Web Framework',
                      'purpose': 'Kubernetes python client',
                      'use_cases': [   'Potentially used for web framework '
                                       'tasks.']},
    'langchain': {   'category': 'Unknown / General',
                     'purpose': 'Building applications with LLMs through '
                                'composability',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'langchain-core': {   'category': 'Unknown / General',
                          'purpose': 'Building applications with LLMs through '
                                     'composability',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'langchain-text-splitters': {   'category': 'Machine Learning',
                                    'purpose': 'LangChain text splitting '
                                               'utilities',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'langcodes': {   'category': 'Unknown / General',
                     'purpose': 'Tools for labeling human languages with IETF '
                                'language tags',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'langsmith': {   'category': 'Machine Learning',
                     'purpose': 'Client library to connect to the LangSmith '
                                'LLM Tracing and Evaluation Platform.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'language_data': {   'category': 'Data Analysis',
                         'purpose': 'Supplementary data about languages used '
                                    'by the langcodes module',
                         'use_cases': [   'Potentially used for data analysis '
                                          'tasks.']},
    'lightning-utilities': {   'category': 'Unknown / General',
                               'purpose': 'Lightning toolbox for across the '
                                          'our ecosystem.',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'litellm': {   'category': 'Web Framework',
                   'purpose': 'Library to easily interface with LLM API '
                              'providers',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'llama-cloud': {   'category': 'Unknown / General',
                       'purpose': 'Auto-discovered Python library named '
                                  "'llama-cloud'. Purpose not yet documented.",
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'llama-cloud-services': {   'category': 'Machine Learning',
                                'purpose': 'Tailored SDK clients for '
                                           'LlamaCloud services.',
                                'use_cases': [   'Potentially used for machine '
                                                 'learning tasks.']},
    'llama-index': {   'category': 'Data Analysis',
                       'purpose': 'Interface between LLMs and your data',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'llama-index-cli': {   'category': 'Unknown / General',
                           'purpose': 'llama-index cli',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'llama-index-core': {   'category': 'Data Analysis',
                            'purpose': 'Interface between LLMs and your data',
                            'use_cases': [   'Potentially used for data '
                                             'analysis tasks.']},
    'llama-index-embeddings-openai': {   'category': 'Machine Learning',
                                         'purpose': 'llama-index embeddings '
                                                    'openai integration',
                                         'use_cases': [   'Potentially used '
                                                          'for machine '
                                                          'learning tasks.']},
    'llama-index-indices-managed-llama-cloud': {   'category': 'Unknown / '
                                                               'General',
                                                   'purpose': 'llama-index '
                                                              'indices '
                                                              'llama-cloud '
                                                              'integration',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'unknown / '
                                                                    'general '
                                                                    'tasks.']},
    'llama-index-instrumentation': {   'category': 'Unknown / General',
                                       'purpose': 'Add your description here',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'llama-index-llms-openai': {   'category': 'Machine Learning',
                                   'purpose': 'llama-index llms openai '
                                              'integration',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'llama-index-readers-file': {   'category': 'Machine Learning',
                                    'purpose': 'llama-index readers file '
                                               'integration',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'llama-index-readers-llama-parse': {   'category': 'Unknown / General',
                                           'purpose': 'llama-index readers '
                                                      'llama-parse integration',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'llama-index-workflows': {   'category': 'Machine Learning',
                                 'purpose': 'An event-driven, async-first, '
                                            'step-based way to control the '
                                            'execution flow of AI applications '
                                            'like Agents.',
                                 'use_cases': [   'Potentially used for '
                                                  'machine learning tasks.']},
    'llama-parse': {   'category': 'Database / Storage',
                       'purpose': 'Parse files into RAG-Optimized formats.',
                       'use_cases': [   'Potentially used for database / '
                                        'storage tasks.']},
    'llama_cpp_python': {   'category': 'Unknown / General',
                            'purpose': 'Python bindings for the llama.cpp '
                                       'library',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'llvmlite': {   'category': 'Unknown / General',
                    'purpose': 'lightweight wrapper around basic LLVM '
                               'functionality',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'mako': {   'category': 'Unknown / General',
                'purpose': 'A super-fast templating language that borrows the '
                           'best ideas from the existing templating languages.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'marisa-trie': {   'category': 'Unknown / General',
                       'purpose': 'Static memory-efficient and fast Trie-like '
                                  'structures for Python.',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'markdown': {   'category': 'Machine Learning',
                    'purpose': "Python implementation of John Gruber's "
                               'Markdown.',
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'markdown-it-py': {   'category': 'Unknown / General',
                          'purpose': 'Python port of markdown-it. Markdown '
                                     'parsing, done right!',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'markupsafe': {   'category': 'Machine Learning',
                      'purpose': 'Safely add untrusted strings to HTML/XML '
                                 'markup.',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'marshmallow': {   'category': 'Data Analysis',
                       'purpose': 'A lightweight library for converting '
                                  'complex datatypes to and from native Python '
                                  'datatypes.',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'matplotlib': {   'category': 'Visualization',
                      'purpose': 'Python plotting package',
                      'use_cases': [   'Potentially used for visualization '
                                       'tasks.']},
    'matplotlib-inline': {   'category': 'Visualization',
                             'purpose': 'Inline Matplotlib backend for Jupyter',
                             'use_cases': [   'Potentially used for '
                                              'visualization tasks.']},
    'mdurl': {   'category': 'Unknown / General',
                 'purpose': 'Markdown URL utilities',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'ml_dtypes': {   'category': 'Machine Learning',
                     'purpose': 'ml_dtypes is a stand-alone implementation of '
                                'several NumPy dtype extensions used in '
                                'machine learning.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'mmh3': {   'category': 'Unknown / General',
                'purpose': 'Python extension for MurmurHash (MurmurHash3), a '
                           'set of fast and robust hash functions.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'more-itertools': {   'category': 'Unknown / General',
                          'purpose': 'More routines for operating on '
                                     'iterables, beyond itertools',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'mpmath': {   'category': 'Unknown / General',
                  'purpose': 'Python library for arbitrary-precision '
                             'floating-point arithmetic',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'multidict': {   'category': 'Unknown / General',
                     'purpose': 'multidict implementation',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'munkres': {   'category': 'Unknown / General',
                   'purpose': 'Munkres (Hungarian) algorithm for the '
                              'Assignment Problem',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'murmurhash': {   'category': 'Unknown / General',
                      'purpose': 'Cython bindings for MurmurHash',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'mypy_extensions': {   'category': 'Unknown / General',
                           'purpose': 'Type system extensions for programs '
                                      'checked with the mypy type checker.',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'nest-asyncio': {   'category': 'Networking',
                        'purpose': 'Patch asyncio to allow nested event loops',
                        'use_cases': [   'Potentially used for networking '
                                         'tasks.']},
    'networkx': {   'category': 'Visualization',
                    'purpose': 'Python package for creating and manipulating '
                               'graphs and networks',
                    'use_cases': ['Potentially used for visualization tasks.']},
    'nltk': {   'category': 'Unknown / General',
                'purpose': 'Natural Language Toolkit',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'nose': {   'category': 'Unknown / General',
                'purpose': 'nose extends unittest to make testing easier',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'numba': {   'category': 'Unknown / General',
                 'purpose': 'compiling Python code using LLVM',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'numpy': {   'category': 'Unknown / General',
                 'purpose': 'Fundamental package for array computing in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'oauthlib': {   'category': 'Security / Encryption',
                    'purpose': 'A generic, spec-compliant, thorough '
                               'implementation of the OAuth request-signing '
                               'logic',
                    'use_cases': [   'Potentially used for security / '
                                     'encryption tasks.']},
    'onnxruntime': {   'category': 'Unknown / General',
                       'purpose': 'ONNX Runtime is a runtime accelerator for '
                                  'Machine Learning models',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'open-interpreter': {   'category': 'Unknown / General',
                            'purpose': 'Let language models run code',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'openai': {   'category': 'Machine Learning',
                  'purpose': 'The official Python library for the openai API',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'openai-whisper': {   'category': 'Unknown / General',
                          'purpose': 'Robust Speech Recognition via '
                                     'Large-Scale Weak Supervision',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'opencv-python': {   'category': 'Unknown / General',
                         'purpose': 'Wrapper package for OpenCV python '
                                    'bindings.',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'opentelemetry-api': {   'category': 'Web Framework',
                             'purpose': 'OpenTelemetry Python API',
                             'use_cases': [   'Potentially used for web '
                                              'framework tasks.']},
    'opentelemetry-exporter-otlp-proto-common': {   'category': 'Unknown / '
                                                                'General',
                                                    'purpose': 'OpenTelemetry '
                                                               'Protobuf '
                                                               'encoding',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'unknown '
                                                                     '/ '
                                                                     'general '
                                                                     'tasks.']},
    'opentelemetry-exporter-otlp-proto-grpc': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'OpenTelemetry '
                                                             'Collector '
                                                             'Protobuf over '
                                                             'gRPC Exporter',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'opentelemetry-proto': {   'category': 'Unknown / General',
                               'purpose': 'OpenTelemetry Python Proto',
                               'use_cases': [   'Potentially used for unknown '
                                                '/ general tasks.']},
    'opentelemetry-sdk': {   'category': 'Unknown / General',
                             'purpose': 'OpenTelemetry Python SDK',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'opentelemetry-semantic-conventions': {   'category': 'Unknown / General',
                                              'purpose': 'OpenTelemetry '
                                                         'Semantic Conventions',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'opt_einsum': {   'category': 'Unknown / General',
                      'purpose': 'Path optimization of einsum functions.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'optree': {   'category': 'Unknown / General',
                  'purpose': 'Optimized PyTree Utilities.',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'optuna': {   'category': 'Unknown / General',
                  'purpose': 'A hyperparameter optimization framework',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'orjson': {   'category': 'Data Analysis',
                  'purpose': 'Fast, correct Python JSON library supporting '
                             'dataclasses, datetimes, and numpy',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'osqp': {   'category': 'Unknown / General',
                'purpose': 'OSQP: The Operator Splitting QP Solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'outcome': {   'category': 'Unknown / General',
                   'purpose': 'Capture the outcome of Python function calls.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'overrides': {   'category': 'Unknown / General',
                     'purpose': 'A decorator to automatically detect mismatch '
                                'when overriding a method.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'packaging': {   'category': 'Unknown / General',
                     'purpose': 'Core utilities for Python packages',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pandas': {   'category': 'Data Analysis',
                  'purpose': 'Powerful data structures for data analysis, time '
                             'series, and statistics',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'parso': {   'category': 'Unknown / General',
                 'purpose': 'A Python Parser',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'pexpect': {   'category': 'Unknown / General',
                   'purpose': 'Pexpect allows easy control of interactive '
                              'console applications.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'pickleshare': {   'category': 'Data Analysis',
                       'purpose': "Tiny 'shelve'-like database with "
                                  'concurrency support',
                       'use_cases': [   'Potentially used for data analysis '
                                        'tasks.']},
    'pillow': {   'category': 'Unknown / General',
                  'purpose': 'Python Imaging Library (Fork)',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pip': {   'category': 'Unknown / General',
               'purpose': 'The PyPA recommended tool for installing Python '
                          'packages.',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'piqp': {   'category': 'Unknown / General',
                'purpose': 'A Proximal Interior Point Quadratic Programming '
                           'solver',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'platformdirs': {   'category': 'Data Analysis',
                        'purpose': 'A small Python package for determining '
                                   'appropriate platform-specific dirs, e.g. a '
                                   '`user data dir`.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'pluggy': {   'category': 'Unknown / General',
                  'purpose': 'plugin and hook calling mechanisms for python',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pomegranate': {   'category': 'Machine Learning',
                       'purpose': 'A PyTorch implementation of probabilistic '
                                  'models.',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'posthog': {   'category': 'Unknown / General',
                   'purpose': 'Integrate PostHog into any python application.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'preshed': {   'category': 'Unknown / General',
                   'purpose': 'Cython hash table that trusts the keys are '
                              'pre-hashed',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'prompt_toolkit': {   'category': 'Unknown / General',
                          'purpose': 'Library for building powerful '
                                     'interactive command lines in Python',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'propcache': {   'category': 'Unknown / General',
                     'purpose': 'Accelerated property cache',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'proto-plus': {   'category': 'Unknown / General',
                      'purpose': 'Beautiful, Pythonic protocol buffers',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'protobuf': {   'category': 'Unknown / General',
                    'purpose': 'Auto-discovered Python library named '
                               "'protobuf'. Purpose not yet documented.",
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'proxsuite': {   'category': 'Unknown / General',
                     'purpose': 'Quadratic Programming Solver for Robotics and '
                                'beyond.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'psutil': {   'category': 'Database / Storage',
                  'purpose': 'Cross-platform lib for process and system '
                             'monitoring in Python.',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'ptyprocess': {   'category': 'Unknown / General',
                      'purpose': 'Run a subprocess in a pseudo terminal',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'pure_eval': {   'category': 'Unknown / General',
                     'purpose': 'Safely evaluate AST nodes without side '
                                'effects',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pyasn1': {   'category': 'Unknown / General',
                  'purpose': 'Pure-Python implementation of ASN.1 types and '
                             'DER/BER/CER codecs (X.208)',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyasn1_modules': {   'category': 'Unknown / General',
                          'purpose': 'A collection of ASN.1-based protocols '
                                     'modules',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'pyaudio': {   'category': 'Database / Storage',
                   'purpose': 'Cross-platform audio I/O with PortAudio',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'pyautogen': {   'category': 'Machine Learning',
                     'purpose': 'A programming framework for agentic AI. Proxy '
                                'package for autogen-agentchat.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pybase64': {   'category': 'Unknown / General',
                    'purpose': 'Fast Base64 encoding/decoding',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pybind11': {   'category': 'Machine Learning',
                    'purpose': 'Seamless operability between C++11 and Python',
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'pybind11-global': {   'category': 'Machine Learning',
                           'purpose': 'Seamless operability between C++11 and '
                                      'Python',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'pycparser': {   'category': 'Unknown / General',
                     'purpose': 'C parser in Python',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pydantic': {   'category': 'Data Analysis',
                    'purpose': 'Data validation using Python type hints',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'pydantic_core': {   'category': 'Unknown / General',
                         'purpose': 'Core functionality for Pydantic '
                                    'validation and serialization',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'pydatalog': {   'category': 'Machine Learning',
                     'purpose': 'A pure-python implementation of Datalog, a '
                                'truly declarative language derived from '
                                'Prolog.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pydub': {   'category': 'Unknown / General',
                 'purpose': 'Manipulate audio with an simple and easy high '
                            'level interface',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'pyenchant': {   'category': 'Unknown / General',
                     'purpose': 'Python bindings for the Enchant spellchecking '
                                'system',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pygments': {   'category': 'Unknown / General',
                    'purpose': 'Pygments is a syntax highlighting package '
                               'written in Python.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'pyobjc': {   'category': 'Unknown / General',
                  'purpose': 'Python<->ObjC Interoperability Module',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'pyobjc-core': {   'category': 'Unknown / General',
                       'purpose': 'Python<->ObjC Interoperability Module',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'pyobjc-framework-accessibility': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework Accessibility '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-accounts': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Accounts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-addressbook': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'AddressBook on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-adservices': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'AdServices on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-adsupport': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'AdSupport on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-applescriptkit': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'AppleScriptKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-applescriptobjc': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'AppleScriptObjC on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-applicationservices': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'ApplicationServices '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-apptrackingtransparency': {   'category': 'Unknown / '
                                                                'General',
                                                    'purpose': 'Wrappers for '
                                                               'the framework '
                                                               'AppTrackingTransparency '
                                                               'on macOS',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'unknown '
                                                                     '/ '
                                                                     'general '
                                                                     'tasks.']},
    'pyobjc-framework-audiovideobridging': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'AudioVideoBridging '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-authenticationservices': {   'category': 'Security / '
                                                               'Encryption',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'AuthenticationServices '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'security '
                                                                    '/ '
                                                                    'encryption '
                                                                    'tasks.']},
    'pyobjc-framework-automaticassessmentconfiguration': {   'category': 'Unknown '
                                                                         '/ '
                                                                         'General',
                                                             'purpose': 'Wrappers '
                                                                        'for '
                                                                        'the '
                                                                        'framework '
                                                                        'AutomaticAssessmentConfiguration '
                                                                        'on '
                                                                        'macOS',
                                                             'use_cases': [   'Potentially '
                                                                              'used '
                                                                              'for '
                                                                              'unknown '
                                                                              '/ '
                                                                              'general '
                                                                              'tasks.']},
    'pyobjc-framework-automator': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Automator on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-avfoundation': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework AVFoundation on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-avkit': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework AVKit '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-avrouting': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'AVRouting on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-backgroundassets': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'BackgroundAssets on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-browserenginekit': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'BrowserEngineKit on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-businesschat': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework BusinessChat on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-calendarstore': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CalendarStore '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-callkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'CallKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-carbon': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Carbon on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-cfnetwork': {   'category': 'Networking',
                                      'purpose': 'Wrappers for the framework '
                                                 'CFNetwork on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'networking tasks.']},
    'pyobjc-framework-cinematic': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Cinematic on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-classkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'ClassKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cloudkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CloudKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cocoa': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the Cocoa '
                                             'frameworks on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-collaboration': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework Collaboration '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-colorsync': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ColorSync on Mac OS X',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-contacts': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Contacts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-contactsui': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'ContactsUI on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-coreaudio': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'CoreAudio on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-coreaudiokit': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreAudioKit on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-corebluetooth': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CoreBluetooth '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-coredata': {   'category': 'Data Analysis',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreData on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'data analysis tasks.']},
    'pyobjc-framework-corehaptics': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'CoreHaptics on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-corelocation': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreLocation on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-coremedia': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'CoreMedia on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-coremediaio': {   'category': 'Machine Learning',
                                        'purpose': 'Wrappers for the framework '
                                                   'CoreMediaIO on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'machine learning '
                                                         'tasks.']},
    'pyobjc-framework-coremidi': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreMIDI on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-coreml': {   'category': 'Machine Learning',
                                   'purpose': 'Wrappers for the framework '
                                              'CoreML on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'pyobjc-framework-coremotion': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'CoreMotion on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-coreservices': {   'category': 'Data Analysis',
                                         'purpose': 'Wrappers for the '
                                                    'framework CoreServices on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for data analysis '
                                                          'tasks.']},
    'pyobjc-framework-corespotlight': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework CoreSpotlight '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-coretext': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreText on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-corewlan': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'CoreWLAN on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-cryptotokenkit': {   'category': 'Security / Encryption',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'CryptoTokenKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for security / '
                                                            'encryption '
                                                            'tasks.']},
    'pyobjc-framework-datadetection': {   'category': 'Data Analysis',
                                          'purpose': 'Wrappers for the '
                                                     'framework DataDetection '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for data analysis '
                                                           'tasks.']},
    'pyobjc-framework-devicecheck': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'DeviceCheck on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-devicediscoveryextension': {   'category': 'Unknown / '
                                                                 'General',
                                                     'purpose': 'Wrappers for '
                                                                'the framework '
                                                                'DeviceDiscoveryExtension '
                                                                'on macOS',
                                                     'use_cases': [   'Potentially '
                                                                      'used '
                                                                      'for '
                                                                      'unknown '
                                                                      '/ '
                                                                      'general '
                                                                      'tasks.']},
    'pyobjc-framework-dictionaryservices': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'DictionaryServices '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-discrecording': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework DiscRecording '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-discrecordingui': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'DiscRecordingUI on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-diskarbitration': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'DiskArbitration on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-dvdplayback': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'DVDPlayback on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-eventkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'Accounts on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-exceptionhandling': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ExceptionHandling on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-executionpolicy': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'ExecutionPolicy on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-extensionkit': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework ExtensionKit on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-externalaccessory': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ExternalAccessory on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-fileprovider': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework FileProvider on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-fileproviderui': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'FileProviderUI on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-findersync': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'FinderSync on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-fsevents': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'FSEvents on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-fskit': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework FSKit '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-gamecenter': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'GameCenter on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-gamecontroller': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'GameController on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-gamekit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'GameKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-gameplaykit': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'GameplayKit on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-healthkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'HealthKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-imagecapturecore': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'ImageCaptureCore on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-inputmethodkit': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'InputMethodKit on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-installerplugins': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'InstallerPlugins on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-instantmessage': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'InstantMessage on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-intents': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'Intents on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-intentsui': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'Intents on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-iobluetooth': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'IOBluetooth on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-iobluetoothui': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework IOBluetoothUI '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-iosurface': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'IOSurface on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-ituneslibrary': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework iTunesLibrary '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-kernelmanagement': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'KernelManagement on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-latentsemanticmapping': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'LatentSemanticMapping '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'pyobjc-framework-launchservices': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'LaunchServices on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-libdispatch': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for libdispatch '
                                                   'on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-libxpc': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for xpc on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-linkpresentation': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'LinkPresentation on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-localauthentication': {   'category': 'Security / '
                                                            'Encryption',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'LocalAuthentication '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'security / '
                                                                 'encryption '
                                                                 'tasks.']},
    'pyobjc-framework-localauthenticationembeddedui': {   'category': 'Security '
                                                                      '/ '
                                                                      'Encryption',
                                                          'purpose': 'Wrappers '
                                                                     'for the '
                                                                     'framework '
                                                                     'LocalAuthenticationEmbeddedUI '
                                                                     'on macOS',
                                                          'use_cases': [   'Potentially '
                                                                           'used '
                                                                           'for '
                                                                           'security '
                                                                           '/ '
                                                                           'encryption '
                                                                           'tasks.']},
    'pyobjc-framework-mailkit': {   'category': 'Machine Learning',
                                    'purpose': 'Wrappers for the framework '
                                               'MailKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'machine learning '
                                                     'tasks.']},
    'pyobjc-framework-mapkit': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'MapKit on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-mediaaccessibility': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'MediaAccessibility '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-mediaextension': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'MediaExtension on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-medialibrary': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework MediaLibrary on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-mediaplayer': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'MediaPlayer on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-mediatoolbox': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework MediaToolbox on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-metal': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework Metal '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-metalfx': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'MetalFX on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-metalkit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'MetalKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-metalperformanceshaders': {   'category': 'Database / '
                                                                'Storage',
                                                    'purpose': 'Wrappers for '
                                                               'the framework '
                                                               'MetalPerformanceShaders '
                                                               'on macOS',
                                                    'use_cases': [   'Potentially '
                                                                     'used for '
                                                                     'database '
                                                                     '/ '
                                                                     'storage '
                                                                     'tasks.']},
    'pyobjc-framework-metalperformanceshadersgraph': {   'category': 'Visualization',
                                                         'purpose': 'Wrappers '
                                                                    'for the '
                                                                    'framework '
                                                                    'MetalPerformanceShadersGraph '
                                                                    'on macOS',
                                                         'use_cases': [   'Potentially '
                                                                          'used '
                                                                          'for '
                                                                          'visualization '
                                                                          'tasks.']},
    'pyobjc-framework-metrickit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'MetricKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-mlcompute': {   'category': 'Machine Learning',
                                      'purpose': 'Wrappers for the framework '
                                                 'MLCompute on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'machine learning '
                                                       'tasks.']},
    'pyobjc-framework-modelio': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'ModelIO on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-multipeerconnectivity': {   'category': 'Unknown / '
                                                              'General',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'MultipeerConnectivity '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'unknown / '
                                                                   'general '
                                                                   'tasks.']},
    'pyobjc-framework-naturallanguage': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'NaturalLanguage on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-netfs': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework NetFS '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-network': {   'category': 'Networking',
                                    'purpose': 'Wrappers for the framework '
                                               'Network on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'networking tasks.']},
    'pyobjc-framework-networkextension': {   'category': 'Networking',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'NetworkExtension on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'networking '
                                                              'tasks.']},
    'pyobjc-framework-notificationcenter': {   'category': 'Unknown / General',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'NotificationCenter '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'unknown / '
                                                                'general '
                                                                'tasks.']},
    'pyobjc-framework-opendirectory': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework OpenDirectory '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-osakit': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'OSAKit on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-oslog': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework OSLog '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-passkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'PassKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-pencilkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'PencilKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-phase': {   'category': 'Unknown / General',
                                  'purpose': 'Wrappers for the framework PHASE '
                                             'on macOS',
                                  'use_cases': [   'Potentially used for '
                                                   'unknown / general tasks.']},
    'pyobjc-framework-photos': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Photos on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-photosui': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'PhotosUI on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-preferencepanes': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'PreferencePanes on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-pushkit': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'PushKit on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-quartz': {   'category': 'Visualization',
                                   'purpose': 'Wrappers for the Quartz '
                                              'frameworks on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'visualization tasks.']},
    'pyobjc-framework-quicklookthumbnailing': {   'category': 'Machine '
                                                              'Learning',
                                                  'purpose': 'Wrappers for the '
                                                             'framework '
                                                             'QuickLookThumbnailing '
                                                             'on macOS',
                                                  'use_cases': [   'Potentially '
                                                                   'used for '
                                                                   'machine '
                                                                   'learning '
                                                                   'tasks.']},
    'pyobjc-framework-replaykit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ReplayKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-safariservices': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'SafariServices on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-safetykit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SafetyKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-scenekit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'SceneKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-screencapturekit': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'ScreenCaptureKit on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-screensaver': {   'category': 'Unknown / General',
                                        'purpose': 'Wrappers for the framework '
                                                   'ScreenSaver on macOS',
                                        'use_cases': [   'Potentially used for '
                                                         'unknown / general '
                                                         'tasks.']},
    'pyobjc-framework-screentime': {   'category': 'Unknown / General',
                                       'purpose': 'Wrappers for the framework '
                                                  'ScreenTime on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'unknown / general '
                                                        'tasks.']},
    'pyobjc-framework-scriptingbridge': {   'category': 'Unknown / General',
                                            'purpose': 'Wrappers for the '
                                                       'framework '
                                                       'ScriptingBridge on '
                                                       'macOS',
                                            'use_cases': [   'Potentially used '
                                                             'for unknown / '
                                                             'general tasks.']},
    'pyobjc-framework-searchkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SearchKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-security': {   'category': 'Security / Encryption',
                                     'purpose': 'Wrappers for the framework '
                                                'Security on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'security / encryption '
                                                      'tasks.']},
    'pyobjc-framework-securityfoundation': {   'category': 'Security / '
                                                           'Encryption',
                                               'purpose': 'Wrappers for the '
                                                          'framework '
                                                          'SecurityFoundation '
                                                          'on macOS',
                                               'use_cases': [   'Potentially '
                                                                'used for '
                                                                'security / '
                                                                'encryption '
                                                                'tasks.']},
    'pyobjc-framework-securityinterface': {   'category': 'Security / '
                                                          'Encryption',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'SecurityInterface on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'security / '
                                                               'encryption '
                                                               'tasks.']},
    'pyobjc-framework-securityui': {   'category': 'Security / Encryption',
                                       'purpose': 'Wrappers for the framework '
                                                  'SecurityUI on macOS',
                                       'use_cases': [   'Potentially used for '
                                                        'security / encryption '
                                                        'tasks.']},
    'pyobjc-framework-sensitivecontentanalysis': {   'category': 'Unknown / '
                                                                 'General',
                                                     'purpose': 'Wrappers for '
                                                                'the framework '
                                                                'SensitiveContentAnalysis '
                                                                'on macOS',
                                                     'use_cases': [   'Potentially '
                                                                      'used '
                                                                      'for '
                                                                      'unknown '
                                                                      '/ '
                                                                      'general '
                                                                      'tasks.']},
    'pyobjc-framework-servicemanagement': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'ServiceManagement on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-sharedwithyou': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework SharedWithYou '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-sharedwithyoucore': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'SharedWithYouCore on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-shazamkit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'ShazamKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-social': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Social on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-soundanalysis': {   'category': 'Unknown / General',
                                          'purpose': 'Wrappers for the '
                                                     'framework SoundAnalysis '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for unknown / '
                                                           'general tasks.']},
    'pyobjc-framework-speech': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Speech on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-spritekit': {   'category': 'Unknown / General',
                                      'purpose': 'Wrappers for the framework '
                                                 'SpriteKit on macOS',
                                      'use_cases': [   'Potentially used for '
                                                       'unknown / general '
                                                       'tasks.']},
    'pyobjc-framework-storekit': {   'category': 'Unknown / General',
                                     'purpose': 'Wrappers for the framework '
                                                'StoreKit on macOS',
                                     'use_cases': [   'Potentially used for '
                                                      'unknown / general '
                                                      'tasks.']},
    'pyobjc-framework-symbols': {   'category': 'Unknown / General',
                                    'purpose': 'Wrappers for the framework '
                                               'Symbols on macOS',
                                    'use_cases': [   'Potentially used for '
                                                     'unknown / general '
                                                     'tasks.']},
    'pyobjc-framework-syncservices': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework SyncServices on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-systemconfiguration': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'SystemConfiguration '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-systemextensions': {   'category': 'Unknown / General',
                                             'purpose': 'Wrappers for the '
                                                        'framework '
                                                        'SystemExtensions on '
                                                        'macOS',
                                             'use_cases': [   'Potentially '
                                                              'used for '
                                                              'unknown / '
                                                              'general '
                                                              'tasks.']},
    'pyobjc-framework-threadnetwork': {   'category': 'Networking',
                                          'purpose': 'Wrappers for the '
                                                     'framework ThreadNetwork '
                                                     'on macOS',
                                          'use_cases': [   'Potentially used '
                                                           'for networking '
                                                           'tasks.']},
    'pyobjc-framework-uniformtypeidentifiers': {   'category': 'Database / '
                                                               'Storage',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'UniformTypeIdentifiers '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'database '
                                                                    '/ storage '
                                                                    'tasks.']},
    'pyobjc-framework-usernotifications': {   'category': 'Unknown / General',
                                              'purpose': 'Wrappers for the '
                                                         'framework '
                                                         'UserNotifications on '
                                                         'macOS',
                                              'use_cases': [   'Potentially '
                                                               'used for '
                                                               'unknown / '
                                                               'general '
                                                               'tasks.']},
    'pyobjc-framework-usernotificationsui': {   'category': 'Unknown / General',
                                                'purpose': 'Wrappers for the '
                                                           'framework '
                                                           'UserNotificationsUI '
                                                           'on macOS',
                                                'use_cases': [   'Potentially '
                                                                 'used for '
                                                                 'unknown / '
                                                                 'general '
                                                                 'tasks.']},
    'pyobjc-framework-videosubscriberaccount': {   'category': 'Unknown / '
                                                               'General',
                                                   'purpose': 'Wrappers for '
                                                              'the framework '
                                                              'VideoSubscriberAccount '
                                                              'on macOS',
                                                   'use_cases': [   'Potentially '
                                                                    'used for '
                                                                    'unknown / '
                                                                    'general '
                                                                    'tasks.']},
    'pyobjc-framework-videotoolbox': {   'category': 'Unknown / General',
                                         'purpose': 'Wrappers for the '
                                                    'framework VideoToolbox on '
                                                    'macOS',
                                         'use_cases': [   'Potentially used '
                                                          'for unknown / '
                                                          'general tasks.']},
    'pyobjc-framework-virtualization': {   'category': 'Unknown / General',
                                           'purpose': 'Wrappers for the '
                                                      'framework '
                                                      'Virtualization on macOS',
                                           'use_cases': [   'Potentially used '
                                                            'for unknown / '
                                                            'general tasks.']},
    'pyobjc-framework-vision': {   'category': 'Unknown / General',
                                   'purpose': 'Wrappers for the framework '
                                              'Vision on macOS',
                                   'use_cases': [   'Potentially used for '
                                                    'unknown / general '
                                                    'tasks.']},
    'pyobjc-framework-webkit': {   'category': 'Web Framework',
                                   'purpose': 'Wrappers for the framework '
                                              'WebKit on macOS',
                                   'use_cases': [   'Potentially used for web '
                                                    'framework tasks.']},
    'pyparsing': {   'category': 'Unknown / General',
                     'purpose': 'pyparsing module - Classes and methods to '
                                'define and execute parsing grammars',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'pypdf': {   'category': 'Database / Storage',
                 'purpose': 'A pure-python PDF library capable of splitting, '
                            'merging, cropping, and transforming PDF files',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'pyperclip': {   'category': 'Machine Learning',
                     'purpose': 'A cross-platform clipboard module for Python. '
                                '(Only handles plain text for now.)',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pypika': {   'category': 'Data Analysis',
                  'purpose': 'A SQL query builder API for Python',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'pyproject_hooks': {   'category': 'Machine Learning',
                           'purpose': 'Wrappers to call pyproject.toml-based '
                                      'build backend hooks.',
                           'use_cases': [   'Potentially used for machine '
                                            'learning tasks.']},
    'pysocks': {   'category': 'Database / Storage',
                   'purpose': 'A Python SOCKS client module. See '
                              'https://github.com/Anorov/PySocks for more '
                              'information.',
                   'use_cases': [   'Potentially used for database / storage '
                                    'tasks.']},
    'pytest': {   'category': 'Unknown / General',
                  'purpose': 'pytest: simple powerful testing with Python',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'python-dateutil': {   'category': 'Unknown / General',
                           'purpose': 'Extensions to the standard Python '
                                      'datetime module',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'python-dotenv': {   'category': 'Machine Learning',
                         'purpose': 'Read key-value pairs from a .env file and '
                                    'set them as environment variables',
                         'use_cases': [   'Potentially used for machine '
                                          'learning tasks.']},
    'python-engineio': {   'category': 'Unknown / General',
                           'purpose': 'Engine.IO server and client for Python',
                           'use_cases': [   'Potentially used for unknown / '
                                            'general tasks.']},
    'python-multipart': {   'category': 'Unknown / General',
                            'purpose': 'A streaming multipart parser for '
                                       'Python',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'python-socketio': {   'category': 'Networking',
                           'purpose': 'Socket.IO server and client for Python',
                           'use_cases': [   'Potentially used for networking '
                                            'tasks.']},
    'pytoolconfig': {   'category': 'Unknown / General',
                        'purpose': 'Python tool configuration',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'pytorchcv': {   'category': 'Machine Learning',
                     'purpose': 'Computer vision models for PyTorch',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'pyttsx3': {   'category': 'Web Framework',
                   'purpose': 'Text to Speech (TTS) library for Python 3. '
                              'Works without internet connection or delay. '
                              'Supports multiple TTS engines, including Sapi5, '
                              'nsss, and espeak.',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'pytz': {   'category': 'Unknown / General',
                'purpose': 'World timezone definitions, modern and historical',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'pyyaml': {   'category': 'Machine Learning',
                  'purpose': 'YAML parser and emitter for Python',
                  'use_cases': [   'Potentially used for machine learning '
                                   'tasks.']},
    'pyzmq': {   'category': 'Unknown / General',
                 'purpose': 'Python bindings for 0MQ',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'qpalm': {   'category': 'Unknown / General',
                 'purpose': 'Proximal Augmented Lagrangian method for '
                            'Quadratic Programs',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'qpax': {   'category': 'Unknown / General',
                'purpose': 'Differentiable QP solver in JAX.',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'qpsolvers': {   'category': 'Web Framework',
                     'purpose': 'Quadratic programming solvers in Python with '
                                'a unified API.',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'quadprog': {   'category': 'Unknown / General',
                    'purpose': 'Quadratic Programming Solver',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'rdflib': {   'category': 'Database / Storage',
                  'purpose': 'RDFLib is a Python library for working with RDF, '
                             'a simple yet powerful language for representing '
                             'information.',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'readchar': {   'category': 'Unknown / General',
                    'purpose': 'Library to easily read single chars and key '
                               'strokes',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'redbaron': {   'category': 'Unknown / General',
                    'purpose': 'Abstraction on top of baron, a FST for python '
                               'to make writing refactoring code a realistic '
                               'task',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'redis': {   'category': 'Data Analysis',
                 'purpose': 'Python client for Redis database and key-value '
                            'store',
                 'use_cases': ['Potentially used for data analysis tasks.']},
    'referencing': {   'category': 'Web Framework',
                       'purpose': 'JSON Referencing + Python',
                       'use_cases': [   'Potentially used for web framework '
                                        'tasks.']},
    'regex': {   'category': 'Unknown / General',
                 'purpose': 'Alternative regular expression module, to replace '
                            're.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'requests': {   'category': 'Networking',
                    'purpose': 'Python HTTP for Humans.',
                    'use_cases': ['Potentially used for networking tasks.']},
    'requests-oauthlib': {   'category': 'Networking',
                             'purpose': 'OAuthlib authentication support for '
                                        'Requests.',
                             'use_cases': [   'Potentially used for networking '
                                              'tasks.']},
    'requests-toolbelt': {   'category': 'Networking',
                             'purpose': 'A utility belt for advanced users of '
                                        'python-requests',
                             'use_cases': [   'Potentially used for networking '
                                              'tasks.']},
    'rich': {   'category': 'Unknown / General',
                'purpose': 'Render rich text, tables, progress bars, syntax '
                           'highlighting, markdown and more to the terminal',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'rope': {   'category': 'Unknown / General',
                'purpose': 'a python refactoring library...',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'rpds-py': {   'category': 'Data Analysis',
                   'purpose': "Python bindings to Rust's persistent data "
                              'structures (rpds)',
                   'use_cases': ['Potentially used for data analysis tasks.']},
    'rply': {   'category': 'Unknown / General',
                'purpose': 'A pure Python Lex/Yacc that works with RPython',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'rsa': {   'category': 'Unknown / General',
               'purpose': 'Pure-Python RSA implementation',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'ruamel.yaml': {   'category': 'Machine Learning',
                       'purpose': 'ruamel.yaml is a YAML parser/emitter that '
                                  'supports roundtrip preservation of '
                                  'comments, seq/map flow style, and map key '
                                  'order',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'ruamel.yaml.clib': {   'category': 'Machine Learning',
                            'purpose': 'C version of reader, parser and '
                                       'emitter for ruamel.yaml derived from '
                                       'libyaml',
                            'use_cases': [   'Potentially used for machine '
                                             'learning tasks.']},
    'ruff': {   'category': 'Database / Storage',
                'purpose': 'An extremely fast Python linter and code '
                           'formatter, written in Rust.',
                'use_cases': [   'Potentially used for database / storage '
                                 'tasks.']},
    'runs': {   'category': 'Unknown / General',
                'purpose': '🏃 Run a block of text as a subprocess 🏃',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'safehttpx': {   'category': 'Unknown / General',
                     'purpose': 'A small Python library created to help '
                                'developers protect their applications from '
                                'Server Side Request Forgery (SSRF) attacks.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'safetensors': {   'category': 'Unknown / General',
                       'purpose': 'Auto-discovered Python library named '
                                  "'safetensors'. Purpose not yet documented.",
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'scikit-learn': {   'category': 'Data Analysis',
                        'purpose': 'A set of python modules for machine '
                                   'learning and data mining',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'scipy': {   'category': 'Unknown / General',
                 'purpose': 'Fundamental algorithms for scientific computing '
                            'in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'scs': {   'category': 'Unknown / General',
               'purpose': 'Splitting conic solver',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'selenium': {   'category': 'Web Framework',
                    'purpose': 'Official Python bindings for Selenium '
                               'WebDriver',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'semantic-version': {   'category': 'Unknown / General',
                            'purpose': "A library implementing the 'SemVer' "
                                       'scheme.',
                            'use_cases': [   'Potentially used for unknown / '
                                             'general tasks.']},
    'send2trash': {   'category': 'Unknown / General',
                      'purpose': 'Send file to trash natively under Mac OS X, '
                                 'Windows and Linux',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'sentence-transformers': {   'category': 'Machine Learning',
                                 'purpose': 'Embeddings, Retrieval, and '
                                            'Reranking',
                                 'use_cases': [   'Potentially used for '
                                                  'machine learning tasks.']},
    'sentencepiece': {   'category': 'Unknown / General',
                         'purpose': 'Unsupervised text tokenizer and '
                                    'detokenizer.',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'sentry-sdk': {   'category': 'Networking',
                      'purpose': 'Python client for Sentry (https://sentry.io)',
                      'use_cases': ['Potentially used for networking tasks.']},
    'setuptools': {   'category': 'Unknown / General',
                      'purpose': 'Easily download, build, install, upgrade, '
                                 'and uninstall Python packages',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'sgmllib3k': {   'category': 'Machine Learning',
                     'purpose': 'Py3k port of sgmllib.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'shellingham': {   'category': 'Unknown / General',
                       'purpose': 'Tool to Detect Surrounding Shell',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'shortuuid': {   'category': 'Unknown / General',
                     'purpose': 'A generator library for concise, unambiguous '
                                'and URL-safe UUIDs.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'simple-websocket': {   'category': 'Web Framework',
                            'purpose': 'Simple WebSocket server and client for '
                                       'Python',
                            'use_cases': [   'Potentially used for web '
                                             'framework tasks.']},
    'sip_python': {   'category': 'Unknown / General',
                      'purpose': 'Python bindings for the SIP solver.',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'six': {   'category': 'Unknown / General',
               'purpose': 'Python 2 and 3 compatibility utilities',
               'use_cases': ['Potentially used for unknown / general tasks.']},
    'smart_open': {   'category': 'Unknown / General',
                      'purpose': 'Utils for streaming large files (S3, HDFS, '
                                 'GCS, SFTP, Azure Blob Storage, gzip, bz2, '
                                 'zst...)',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'smmap': {   'category': 'Unknown / General',
                 'purpose': 'A pure Python implementation of a sliding window '
                            'memory map manager',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'sniffio': {   'category': 'Networking',
                   'purpose': 'Sniff out which async library your code is '
                              'running under',
                   'use_cases': ['Potentially used for networking tasks.']},
    'sortedcontainers': {   'category': 'Machine Learning',
                            'purpose': 'Sorted Containers -- Sorted List, '
                                       'Sorted Dict, Sorted Set',
                            'use_cases': [   'Potentially used for machine '
                                             'learning tasks.']},
    'soupsieve': {   'category': 'Machine Learning',
                     'purpose': 'A modern CSS selector implementation for '
                                'Beautiful Soup.',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'spacy': {   'category': 'Unknown / General',
                 'purpose': 'Industrial-strength Natural Language Processing '
                            '(NLP) in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'spacy-legacy': {   'category': 'Unknown / General',
                        'purpose': 'Legacy registered functions for spaCy '
                                   'backwards compatibility',
                        'use_cases': [   'Potentially used for unknown / '
                                         'general tasks.']},
    'spacy-loggers': {   'category': 'Unknown / General',
                         'purpose': 'Logging utilities for SpaCy',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'speechrecognition': {   'category': 'Web Framework',
                             'purpose': 'Library for performing speech '
                                        'recognition, with support for several '
                                        'engines and APIs, online and offline.',
                             'use_cases': [   'Potentially used for web '
                                              'framework tasks.']},
    'sqlalchemy': {   'category': 'Data Analysis',
                      'purpose': 'Database Abstraction Library',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'sqlmodel': {   'category': 'Data Analysis',
                    'purpose': 'SQLModel, SQL databases in Python, designed '
                               'for simplicity, compatibility, and robustness.',
                    'use_cases': ['Potentially used for data analysis tasks.']},
    'srsly': {   'category': 'Database / Storage',
                 'purpose': 'Modern high-performance serialization utilities '
                            'for Python',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'stack-data': {   'category': 'Data Analysis',
                      'purpose': 'Extract data from python stack frames and '
                                 'tracebacks for informative displays',
                      'use_cases': [   'Potentially used for data analysis '
                                       'tasks.']},
    'starlette': {   'category': 'Unknown / General',
                     'purpose': 'The little ASGI library that shines.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'striprtf': {   'category': 'Unknown / General',
                    'purpose': 'A simple library to convert rtf to text',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'sympy': {   'category': 'Unknown / General',
                 'purpose': 'Computer algebra system (CAS) in Python',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'tenacity': {   'category': 'Unknown / General',
                    'purpose': 'Retry code until it succeeds',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'tensorboard': {   'category': 'Machine Learning',
                       'purpose': 'TensorBoard lets you watch Tensors Flow',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'tensorboard-data-server': {   'category': 'Machine Learning',
                                   'purpose': 'Fast data loading for '
                                              'TensorBoard',
                                   'use_cases': [   'Potentially used for '
                                                    'machine learning tasks.']},
    'termcolor': {   'category': 'Database / Storage',
                     'purpose': 'ANSI color formatting for output in terminal',
                     'use_cases': [   'Potentially used for database / storage '
                                      'tasks.']},
    'textblob': {   'category': 'Unknown / General',
                    'purpose': 'Simple, Pythonic text processing. Sentiment '
                               'analysis, part-of-speech tagging, noun phrase '
                               'parsing, and more.',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'thinc': {   'category': 'Machine Learning',
                 'purpose': 'A refreshing functional take on deep learning, '
                            'compatible with your favorite libraries',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'threadpoolctl': {   'category': 'Unknown / General',
                         'purpose': 'threadpoolctl',
                         'use_cases': [   'Potentially used for unknown / '
                                          'general tasks.']},
    'tiktoken': {   'category': 'Machine Learning',
                    'purpose': 'tiktoken is a fast BPE tokeniser for use with '
                               "OpenAI's models",
                    'use_cases': [   'Potentially used for machine learning '
                                     'tasks.']},
    'tokenizers': {   'category': 'Machine Learning',
                      'purpose': 'Auto-discovered Python library named '
                                 "'tokenizers'. Purpose not yet documented.",
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'tokentrim': {   'category': 'Unknown / General',
                     'purpose': "Easily trim 'messages' arrays for use with "
                                'GPTs.',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']},
    'toml': {   'category': 'Unknown / General',
                'purpose': "Python Library for Tom's Obvious, Minimal Language",
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'tomlkit': {   'category': 'Machine Learning',
                   'purpose': 'Style preserving TOML library',
                   'use_cases': [   'Potentially used for machine learning '
                                    'tasks.']},
    'torch': {   'category': 'Machine Learning',
                 'purpose': 'Tensors and Dynamic neural networks in Python '
                            'with strong GPU acceleration',
                 'use_cases': ['Potentially used for machine learning tasks.']},
    'torchaudio': {   'category': 'Machine Learning',
                      'purpose': 'An audio package for PyTorch',
                      'use_cases': [   'Potentially used for machine learning '
                                       'tasks.']},
    'torchmetrics': {   'category': 'Machine Learning',
                        'purpose': 'PyTorch native Metrics',
                        'use_cases': [   'Potentially used for machine '
                                         'learning tasks.']},
    'torchvision': {   'category': 'Machine Learning',
                       'purpose': 'image and video datasets and models for '
                                  'torch deep learning',
                       'use_cases': [   'Potentially used for machine learning '
                                        'tasks.']},
    'tornado': {   'category': 'Web Framework',
                   'purpose': 'Tornado is a Python web framework and '
                              'asynchronous networking library, originally '
                              'developed at FriendFeed.',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'tqdm': {   'category': 'Unknown / General',
                'purpose': 'Fast, Extensible Progress Meter',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'traitlets': {   'category': 'Machine Learning',
                     'purpose': 'Traitlets Python configuration system',
                     'use_cases': [   'Potentially used for machine learning '
                                      'tasks.']},
    'transformers': {   'category': 'Machine Learning',
                        'purpose': 'State-of-the-art Machine Learning for JAX, '
                                   'PyTorch and TensorFlow',
                        'use_cases': [   'Potentially used for machine '
                                         'learning tasks.']},
    'trio': {   'category': 'Networking',
                'purpose': 'A friendly Python library for async concurrency '
                           'and I/O',
                'use_cases': ['Potentially used for networking tasks.']},
    'trio-websocket': {   'category': 'Web Framework',
                          'purpose': 'WebSocket library for Trio',
                          'use_cases': [   'Potentially used for web framework '
                                           'tasks.']},
    'truststore': {   'category': 'Unknown / General',
                      'purpose': 'Verify certificates using native system '
                                 'trust stores',
                      'use_cases': [   'Potentially used for unknown / general '
                                       'tasks.']},
    'typer': {   'category': 'Unknown / General',
                 'purpose': 'Typer, build great CLIs. Easy to code. Based on '
                            'Python type hints.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'typing-inspect': {   'category': 'Unknown / General',
                          'purpose': 'Runtime inspection utilities for typing '
                                     'module.',
                          'use_cases': [   'Potentially used for unknown / '
                                           'general tasks.']},
    'typing-inspection': {   'category': 'Unknown / General',
                             'purpose': 'Runtime typing introspection tools',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'typing_extensions': {   'category': 'Unknown / General',
                             'purpose': 'Backported and Experimental Type '
                                        'Hints for Python 3.9+',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'tzdata': {   'category': 'Data Analysis',
                  'purpose': 'Provider of IANA time zone data',
                  'use_cases': ['Potentially used for data analysis tasks.']},
    'tzlocal': {   'category': 'Unknown / General',
                   'purpose': 'tzinfo object for the local timezone',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'unicodedata2': {   'category': 'Data Analysis',
                        'purpose': 'Unicodedata backport updated to the latest '
                                   'Unicode version.',
                        'use_cases': [   'Potentially used for data analysis '
                                         'tasks.']},
    'uritemplate': {   'category': 'Unknown / General',
                       'purpose': 'Implementation of RFC 6570 URI Templates',
                       'use_cases': [   'Potentially used for unknown / '
                                        'general tasks.']},
    'urllib3': {   'category': 'Networking',
                   'purpose': 'HTTP library with thread-safe connection '
                              'pooling, file post, and more.',
                   'use_cases': ['Potentially used for networking tasks.']},
    'uvicorn': {   'category': 'Unknown / General',
                   'purpose': 'The lightning-fast ASGI server.',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'uvloop': {   'category': 'Networking',
                  'purpose': 'Fast implementation of asyncio event loop on top '
                             'of libuv',
                  'use_cases': ['Potentially used for networking tasks.']},
    'wandb': {   'category': 'Web Framework',
                 'purpose': 'A CLI and library for interacting with the '
                            'Weights & Biases API.',
                 'use_cases': ['Potentially used for web framework tasks.']},
    'wasabi': {   'category': 'Database / Storage',
                  'purpose': 'A lightweight console printing and formatting '
                             'toolkit',
                  'use_cases': [   'Potentially used for database / storage '
                                   'tasks.']},
    'watchdog': {   'category': 'Unknown / General',
                    'purpose': 'Filesystem events monitoring',
                    'use_cases': [   'Potentially used for unknown / general '
                                     'tasks.']},
    'watchfiles': {   'category': 'Database / Storage',
                      'purpose': 'Simple, modern and high performance file '
                                 'watching and code reload in python.',
                      'use_cases': [   'Potentially used for database / '
                                       'storage tasks.']},
    'wcwidth': {   'category': 'Unknown / General',
                   'purpose': 'Measures the displayed width of unicode strings '
                              'in a terminal',
                   'use_cases': [   'Potentially used for unknown / general '
                                    'tasks.']},
    'weasel': {   'category': 'Unknown / General',
                  'purpose': 'Weasel: A small and easy workflow system',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'webdriver-manager': {   'category': 'Unknown / General',
                             'purpose': 'Library provides the way to '
                                        'automatically manage drivers for '
                                        'different browsers',
                             'use_cases': [   'Potentially used for unknown / '
                                              'general tasks.']},
    'websocket-client': {   'category': 'Web Framework',
                            'purpose': 'WebSocket client for Python with low '
                                       'level API options',
                            'use_cases': [   'Potentially used for web '
                                             'framework tasks.']},
    'websockets': {   'category': 'Web Framework',
                      'purpose': 'An implementation of the WebSocket Protocol '
                                 '(RFC 6455 & 7692)',
                      'use_cases': [   'Potentially used for web framework '
                                       'tasks.']},
    'werkzeug': {   'category': 'Web Framework',
                    'purpose': 'The comprehensive WSGI web application '
                               'library.',
                    'use_cases': ['Potentially used for web framework tasks.']},
    'wget': {   'category': 'Unknown / General',
                'purpose': 'pure python download utility',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'wheel': {   'category': 'Database / Storage',
                 'purpose': 'A built-package format for Python',
                 'use_cases': [   'Potentially used for database / storage '
                                  'tasks.']},
    'wikipedia': {   'category': 'Web Framework',
                     'purpose': 'Wikipedia API for Python',
                     'use_cases': [   'Potentially used for web framework '
                                      'tasks.']},
    'wrapt': {   'category': 'Unknown / General',
                 'purpose': 'Module for decorators, wrappers and monkey '
                            'patching.',
                 'use_cases': [   'Potentially used for unknown / general '
                                  'tasks.']},
    'wsproto': {   'category': 'Web Framework',
                   'purpose': 'WebSockets state-machine based protocol '
                              'implementation',
                   'use_cases': ['Potentially used for web framework tasks.']},
    'xmod': {   'category': 'Unknown / General',
                'purpose': '🌱 Turn any object into a module 🌱',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'yarl': {   'category': 'Unknown / General',
                'purpose': 'Yet another URL library',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'yaspin': {   'category': 'Unknown / General',
                  'purpose': 'Yet Another Terminal Spinner',
                  'use_cases': [   'Potentially used for unknown / general '
                                   'tasks.']},
    'zipp': {   'category': 'Unknown / General',
                'purpose': 'Backport of pathlib-compatible object wrapper for '
                           'zip files',
                'use_cases': ['Potentially used for unknown / general tasks.']},
    'zstandard': {   'category': 'Unknown / General',
                     'purpose': 'Zstandard bindings for Python',
                     'use_cases': [   'Potentially used for unknown / general '
                                      'tasks.']}}


# --- Heuristic & metadata-based summary generation ---
def guess_category(summary: str, keywords: str) -> str:
    text = f"{summary or ''} {keywords or ''}".lower()
    if any(k in text for k in ["neural", "ml", "ai", "deep learning", "torch", "tensorflow"]):
        return "Machine Learning"
    if any(k in text for k in ["data", "pandas", "csv", "excel"]):
        return "Data Analysis"
    if any(k in text for k in ["web", "api", "flask", "fastapi", "django"]):
        return "Web Framework"
    if any(k in text for k in ["plot", "chart", "graph", "visual"]):
        return "Visualization"
    if any(k in text for k in ["database", "sql", "orm"]):
        return "Database / Storage"
    if any(k in text for k in ["async", "socket", "network", "http", "requests"]):
        return "Networking"
    if any(k in text for k in ["crypto", "encrypt", "auth", "security"]):
        return "Security / Encryption"
    return "Unknown / General"

# --- Ollama description fallback ---
def call_ollama_for_description(package_name: str) -> str:
    """
    Calls Ollama to get a description for a library.
    Replace with your local setup or API call.
    """
    try:
        result = subprocess.run(
            ["ollama", "query", "gpt-5-mini",
             f"Provide a short, clear description of the Python library '{package_name}'."],
            capture_output=True, text=True, check=True
        )
        description = result.stdout.strip()
        if description:
            return description
    except Exception as e:
        print(f"[Echo] Ollama call failed for {package_name}: {e}")
    # Fallback
    return f"Auto-discovered Python library named '{package_name}'. Purpose not yet documented."

# --- Summary generation ---
def generate_summary(package_name: str):
    try:
        meta = importlib.metadata.metadata(package_name)
        summary = meta.get("Summary", "").strip()
        keywords = meta.get("Keywords", "")
        category = guess_category(summary, keywords)
    except Exception:
        summary = ""
        category = "Unknown / General"
        keywords = ""

    if not summary:
        summary = call_ollama_for_description(package_name)
        category = guess_category(summary, keywords)

    return {
        "category": category,
        "purpose": summary,
        "use_cases": [f"Potentially used for {category.lower()} tasks."]
    }

# --- Discovery of new libraries ---
def discover_new_libraries():
    discovered = []
    for dist in importlib.metadata.distributions():
        try:
            name = dist.metadata["Name"].lower()
        except KeyError:
            continue
        if name not in LIBRARY_KNOWLEDGE:
            LIBRARY_KNOWLEDGE[name] = generate_summary(name)
            discovered.append(name)
    if discovered:
        for name in discovered:
            print(f"[Echo] 🧩 Discovered new cognitive organ: {name}")
    return discovered

# --- Self-updating mechanism ---
def update_file(discovered):
    if not discovered:
        return
    filepath = os.path.abspath(__file__)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Rebuild full dictionary text safely
    lib_text = pprint.pformat(LIBRARY_KNOWLEDGE, indent=4)

    # Replace entire LIBRARY_KNOWLEDGE block
    with open(filepath, "r") as f:
        content = f.read()

    if "LIBRARY_KNOWLEDGE = {" in content:
        before, _, after = content.partition("LIBRARY_KNOWLEDGE = {")
        after = after.split("}", 1)[-1]  # Keep content after closing brace
        updated = before + "LIBRARY_KNOWLEDGE = " + lib_text + "\n" + after
    else:
        updated = content + f"\n\nLIBRARY_KNOWLEDGE = " + lib_text + "\n"

    with open(filepath, "w") as f:
        f.write(updated)

    print(f"[Echo] Library knowledge updated with {len(discovered)} new entries ({timestamp}).")

# --- Library description ---
def describe_library(lib_name: str):
    info = LIBRARY_KNOWLEDGE.get(lib_name.lower())
    if not info:
        return f"No entry found for '{lib_name}'."
    summary = f"{lib_name} ({info['category']}): {info['purpose']}"
    if "use_cases" in info:
        summary += "\nUse cases:\n  - " + "\n  - ".join(info["use_cases"])
    return textwrap.dedent(summary)

# --- Auto-update trigger ---
new_libs = discover_new_libraries()
update_file(new_libs)

