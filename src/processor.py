#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import re

from sqlalchemy import Column, Integer, String, Float, func
from sqlalchemy import create_engine, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

db_url = 'mysql://' + \
         os.environ['DB_USER'] + ':' + \
         os.environ['DB_PASSWORD'] + '@' + \
         os.environ['DB_URL'] + '/' + \
         os.environ['DB_DATABASE']

engine = create_engine(db_url)

Base = declarative_base()


# model classes
class Repository(Base):
    __tablename__ = 'Repositories'
    Id = Column(Integer, primary_key=True)
    Name = Column(String(100))
    Description = Column(String(100))
    Languages = relationship('RepositoryLanguage', back_populates='Repository')


class Insult(Base):
    __tablename__ = 'Insults'
    Id = Column(Integer, primary_key=True)
    Text = Column(String(100))
    Regex = Column(String(200))
    Languages = relationship('LanguageInsult', back_populates='Insult')


class Language(Base):
    __tablename__ = 'Languages'
    Id = Column(Integer, primary_key=True)
    Name = Column(String(100))
    Repositories = relationship('RepositoryLanguage', back_populates='Language')
    Insults = relationship('LanguageInsult', back_populates='Language')


class RepositoryLanguage(Base):
    __tablename__ = 'RepositoryLanguages'
    LanguageId = Column(Integer, ForeignKey('Languages.Id'), primary_key=True)
    RepositoryId = Column(Integer, ForeignKey('Repositories.Id'), primary_key=True)
    Size_in_Bytes = Column(Integer)
    Repository = relationship('Repository', back_populates='Languages')
    Language = relationship('Language', back_populates='Repositories')


class LanguageInsult(Base):
    __tablename__ = 'LanguageInsults'
    LanguageId = Column(Integer, ForeignKey('Languages.Id'), primary_key=True)
    InsultId = Column(Integer, ForeignKey('Insults.Id'), primary_key=True)
    Occurence = Column(Float)
    Language = relationship('Language', back_populates='Insults')
    Insult = relationship('Insult', back_populates='Languages')


def parse_json(file, session):
    parsed_json = json.load(file)

    repo_id = parsed_json['meta']['id']
    repo_name = parsed_json['meta']['full_name']
    repo_description = parsed_json['meta']['description']

    # stop if repository already exists in database
    if session.query(Repository).filter(Repository.Id == repo_id).first() is not None:
        return

    # new repository
    print('Creating repository...', end='')
    session.add(
        Repository(Id=repo_id, Name=repo_name, Description=repo_description))
    session.commit()
    db_repository = session.query(Repository).filter(Repository.Id == repo_id).first()
    print(' ✓')

    # in repo used programming languages
    print('Processing languages...', end='')
    for lanugage, size in parsed_json['languages'].items():
        db_language = session.query(Language).filter(Language.Name == lanugage).first()
        # use existing language entry, else create a new one
        if db_language is None:
            db_language = Language(Name=lanugage)
            session.add(db_language)
            session.commit()
        # create new connection between repository and language
        session.add(RepositoryLanguage(Repository=db_repository, Language=db_language, Size_in_Bytes=size))
        session.commit()
    print(' ✓')

    repo_size = 0
    for language_size in session.query.with_entities(RepositoryLanguage.Size_in_Bytes).filter(
            Repository.Id == db_repository.Id).all():
        repo_size += language_size
    # dictionary with 'Language' : 'percentage on repo'
    repo_lang_procent = {}
    for repo_language in session.query(RepositoryLanguage).filter(Repository.Id == db_repository.Id):
        language = session.query(Language).filter(Language.Id == repo_language.LanguageId).one()
        repo_lang_procent.update(language=repo_language.Size_In_Bytes / repo_size)

    for repo_language in session.query(RepositoryLanguage).filter(Repository.Id == db_repository.Id).all():
        for insult in session.query(Insult).all():
            # count insult occurences in all commits
            regex = re.compile(insult.Regex, re.IGNORECASE)
            insult_counter = 0
            for commit_sha, commit_values in parsed_json['commits'].items():
                insult_counter += len(re.findall(regex, commit_values['message']))
            # add insult_counter to Language-Insult connection
            language_insult = session.query(LanguageInsult).filter(
                LanguageInsult.LanguageId == repo_language.LanguageId and
                LanguageInsult.InsultId == insult.Id).one_or_none()
            if language_insult is None:
                insult_factor = insult_counter * repo_lang_procent[repo_language]
                LanguageInsult(Language=repo_language, Insult=insult, Occurence=insult_factor)
            else:
                language_insult.Occurence += insult_counter * repo_lang_procent[repo_language]
            session.commit()


def main():
    Base.metadata.bind = engine
    # delete all tables (for testing purpose)
    Base.metadata.drop_all()
    # create missing database tables
    Base.metadata.create_all()

    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(Insult(Text='fuck', Regex='fuck'))

    with open("tmp/876.json") as json_file:
        parse_json(json_file, session)


if __name__ == '__main__':
    main()
