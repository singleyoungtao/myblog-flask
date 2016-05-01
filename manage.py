#!/usr/bin/env python
#-*-coding: utf-8 -*-
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')   
    #启动覆盖检测引擎，buanch开启分支覆盖，include限制分析范围
    COV.start()

from app import create_app, db
from app.models import User, Role, Permission, Post, Follow, Comment
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():   #shell命令注册的回调函数，注册了程序、数据库实例、模型
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Comment=Comment, Post=Post)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """运行单元测试"""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """运行代码分析器下的应用程序"""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                        profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """运行部署任务"""
    from flask.ext.migrate import upgrade
    from app.models import Role, User

    #把数据库迁移到最新修订版本
    upgrade()

    #创建用户角色
    Role.insert_roles()

    #让所有用户都关注此用户
    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
