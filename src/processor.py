#!/usr/bin/python
# -*- coding: utf-8 -*-
import decimal
import json
import os
import re

from sqlalchemy import Column, Integer, String, Float, func, Text
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from src.ftp_manager import download_repo, remove_repo

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
    Name = Column(String(140))
    Description = Column(Text)
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
    Size = Column(Integer)
    Repository = relationship('Repository', back_populates='Languages')
    Language = relationship('Language', back_populates='Repositories')


class LanguageInsult(Base):
    __tablename__ = 'LanguageInsults'
    LanguageId = Column(Integer, ForeignKey('Languages.Id'), primary_key=True)
    InsultId = Column(Integer, ForeignKey('Insults.Id'), primary_key=True)
    Occurrence = Column(Float)
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
        session.add(RepositoryLanguage(Repository=db_repository, Language=db_language, Size=size))
        session.commit()
    print(' ✓')

    print('Processing insults...', end='')
    repo_size_in_bytes = session.query(func.sum(RepositoryLanguage.Size)).filter(
        Repository.Id == db_repository.Id).scalar()
    # dictionary with 'Language' : 'percentage on repo'
    repo_lang_sizes_in_percent = {}
    for repo_language in session.query(RepositoryLanguage).filter(Repository.Id == db_repository.Id).all():
        repo_lang_sizes_in_percent[repo_language.LanguageId] = repo_language.Size / repo_size_in_bytes

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
                insult_factor = insult_counter * repo_lang_sizes_in_percent[repo_language.LanguageId]
                language_insult = LanguageInsult(LanguageId=repo_language.LanguageId, InsultId=insult.Id,
                                                 Occurrence=insult_factor)
                session.add(language_insult)
            else:
                language_insult.Occurrence += insult_counter * float(repo_lang_sizes_in_percent[repo_language.LanguageId])
            session.commit()
    print(' ✓')


def main(repo_id):
    Base.metadata.bind = engine
    # delete all tables (for testing purpose)
    # Base.metadata.drop_all()
    # create missing database tables
    Base.metadata.create_all()

    Session = sessionmaker(bind=engine)
    session = Session()

    # session.add(Insult(Text='fuck', Regex='fuck'))

    download_repo(repo_id)
    with open(os.environ['FTP_LOCAL_DIR'] + '/' + str(repo_id) + '.json') as json_file:
        parse_json(json_file, session)
    remove_repo(repo_id)


def lambda_handler(event, context):
    for record in event['Records']:
        message_attributes = record['messageAttributes']
        repo_id = message_attributes['repo_id']

        main(repo_id)

    return {
        'statusCode': 200,
        'body': json.dumps('Processed repo #' + str(repo_id))
    }


if __name__ == '__main__':
    main(1)
