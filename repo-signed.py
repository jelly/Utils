#!/usr/bin/env python

from pycman import config,pkginfo


class RepoStats():
    
    def __init__(self, db=None):
        self.pkgs=[]
        self.db=db
        for pkg in self.db.search(''):
            self.pkgs.append(pkg)

    def getSigSum(self):
        yay=0
        nay=0
        all=self.pkgs.__len__()
        for p in self.pkgs:
            if p.base64_sig:
                yay+=1
            else:
                nay+=1
        return yay, nay, all


class Repos():
    def __init__(self):
        self.rstats={}
        self.handle=None
        self.handle=config.init_with_config('/etc/pacman.conf')
        for db in self.handle.get_syncdbs():
            self.rstats[db.name]=RepoStats(db)

    def getSigSums(self):
        ## ret=[('repo','signed', 'unsigned', 'all')]
        ret =[]
        for name,a in self.rstats.items():
            y,n,all= a.getSigSum()
            ret.append((name , y, n, all))
        return ret

    def getSigPerc(self):
        ret = []
        for name, yes, no, all in self.getSigSums():
            try:  ret.append((name, 100 * float(yes) / float(all)))
            except ZeroDivisionError: ret.append((name, 0))
        return ret


if __name__ == '__main__':
    r=Repos()
    for name, perc in r.getSigPerc():
        length = 18 - len(name)
        
        print (name, length * ' ', int(perc), '%')
