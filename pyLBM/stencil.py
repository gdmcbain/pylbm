# Authors:
#     Loic Gouarin <loic.gouarin@math.u-psud.fr>
#     Benjamin Graille <benjamin.graille@math.u-psud.fr>
#
# License: BSD 3 clause

import numpy as np
from math import sqrt
import viewer
import utils
import logging

def permute_in_place(a):
    """
    Function permute_in_place
    input: a object of type list
    output: the set of all permutations of this list
    the set is not created in the memory, so it can just be used in a loop
    """
    a.sort()
    yield list(a)

    if len(a) <= 1:
        return

    first = 0
    last = len(a)
    while 1:
        i = last - 1

        while 1:
            i = i - 1
            if a[i] < a[i + 1]:
                j = last - 1
                while not (a[i] < a[j]):
                    j = j - 1
                a[i], a[j] = a[j], a[i] # swap the values
                r = a[i + 1:last]
                r.reverse()
                a[i + 1:last] = r
                yield list(a)
                break
            if i == first:
                a.reverse()
                return

class Velocity(object):
    """
    Create a velocity.

    Parameters
    ----------
    dim : int, optional
         The dimension of the velocity.
    num : int, optional
         The number of the velocity in the numbering convention of Lattice-Boltzmann scheme.
    vx : int, optional
         The x component of the velocity vector.
    vy : int, optional
         The y component of the velocity vector.
    vz : int, optional
         The z component of the velocity vector.

    Attributes
    ----------
    dim : The dimension of the velocity.
    num : The number of the velocity in the numbering convention of Lattice-Boltzmann scheme.
    vx : The x component of the velocity vector.
    vy : The y component of the velocity vector.
    vz : The z component of the velocity vector.

    Methods
    -------
    get_symmetric
        return the symmetric velocity with a direction

    Examples
    --------

    Create a velocity with the dimension and the number

    >>> v = Velocity(dim = 1, num = 2)
    >>> v
    velocity 2
     vx: -1

    Create a velocity with a direction

    >>> v = Velocity(vx=1, vy=1)
    >>> v
    velocity 5
     vx: 1
     vy: 1

    """
    _d = 1e3
    _R2 = np.array([[[5, 6, 4], [_d, _d, 2], [2, 5, 3]],
                    [[3, _d, _d], [_d, -1, _d], [1, _d, _d]],
                    [[6, 7, 7], [_d, _d, 0], [1, 4, 0]]], dtype=np.int)

    def __init__(self, dim=None, num=None, vx=None, vy=None, vz=None):
        self.dim = dim
        self.num = num

        self.vx = vx
        self.vy = vy
        self.vz = vz

        if dim is None:
            if vz is not None:
                self.dim = 3
            elif vy is not None:
                self.dim = 2
            elif vx is not None:
                self.dim = 1
            else:
                raise TypeError('The parameters could not be all None when creating a velocity')

        if num is None:
            self._set_num()
        if vx is None:
            self._set_coord()

    @property
    def v(self):
        l = [self.vx, self.vy, self.vz]
        return l[:self.dim]

    def __str__(self):
        s = '(%d: %d'%(self.num, self.vx)
        if self.vy is not None:
            s += ', %d'%self.vy
        if self.vz is not None:
            s += ', %d'%self.vz
        s += ')'
        return s

    def get_symmetric(self, axis=None):
        """
        return the symmetric velocity.

        Parameters
        ----------

        axis : if None, get the symmetric with the origin
               if 0, get the symmetric with the x axis
               if 1, get the symmetric with the y axis
               if 2, get the symmetric with the z axis

        Returns
        -------

        The symmetric of the velocity

        """
        if axis >= self.dim:
            raise ValueError("axis must be less than the dimension of the velocity (axis:%d, dim:%d)"%(axis, self.dim))

        svx = -self.vx
        svy = None if self.vy is None else -self.vy
        svz = None if self.vz is None else -self.vz

        if axis is None:
            return Velocity(vx=svx, vy=svy, vz=svz)
        if axis == 0:
            return Velocity(vx=self.vx, vy=svy, vz=svz)
        if axis == 1:
            return Velocity(vx=svx, vy=self.vy, vz=svz)
        if axis == 2:
            return Velocity(vx=svx, vy=svy, vz=self.vz)

    def _set_num(self):
        if self.dim == 1:
            avx = abs(self.vx)
            self.num = (2*avx) - (1 if self.vx>0 else 0)
        elif self.dim == 2:
            avx = abs(self.vx)
            avy = abs(self.vy)
            T1 = cmp(self.vx, 0)
            T2 = cmp(self.vy, 0)
            T3 = cmp(avx, avy)
            p = (2*max(avx, avy) - 1)
            p *= p
            q = 8*min(avx, avy)*abs(T3)
            r = self._R2[T1 + 1, T2 + 1, T3 + 1]
            self.num = int(p + q + r)
        elif self.dim == 3:
            count = 0
            sign = [1, -1]
            for k in xrange(10):
                for i in xrange(k + 1):
                    for j in xrange(i + 1):
                        for (kk, ii, jj) in permute_in_place([k, i, j]):
                            for pmk in sign[0: kk + 1]: # loop over + and - if kk > 0
                                for pmi in sign[0:ii + 1]: # loop over + and - if ii > 0
                                    for pmj in sign[0:jj + 1]: # loop over + and - if jj > 0
                                        if self.vx == pmk*kk and self.vy == pmi*ii and self.vz == pmj*jj:
                                            self.num = count
                                            return
                                        else:
                                            count +=1

    def _set_coord(self):
        if self.dim == 1:
            n = self.num + 1
            self.vx = (1 - 2*(n % 2))*(n / 2)
        elif self.dim == 2:
            n = (int)(sqrt(self.num)+1)/2
            p = self.num - (2*n-1)**2
            if (p<4):
                Lx, Ly = [n, 0, -n, 0], [0, n, 0, -n]
                vx, vy = Lx[p], Ly[p]
            elif (p<8):
                Lx, Ly = [n, -n, -n, n], [n, n, -n, -n]
                vx, vy = Lx[p-4], Ly[p-4]
            else:
                k, l = n, p/8
                Lx, Ly = [k, l, -l, -k, -k, -l, l, k], [l, k, k, l, -l, -k, -k, -l]
                vx, vy = Lx[p%8], Ly[p%8]
            self.vx = vx
            self.vy = vy
        elif self.dim == 3:
            count = 0
            sign = [1, -1]
            for k in xrange(10):
                for i in xrange(k + 1):
                    for j in xrange(i + 1):
                        for (kk, ii, jj) in permute_in_place([k, i, j]):
                            for pmk in sign[0:kk + 1]: # loop over + and - if kk > 0
                                for pmi in sign[0:ii + 1]: # loop over + and - if ii > 0
                                    for pmj in sign[0:jj + 1]: # loop over + and - if jj > 0
                                        if self.num == count:
                                            self.vx = pmk*kk
                                            self.vy = pmi*ii
                                            self.vz = pmj*jj
                                            return
                                        else:
                                            count +=1

class itemproperty(property):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super(itemproperty, self).__init__(fget, fset, fdel, doc)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        else:
            return bounditemproperty(self, obj)

class bounditemproperty(property):
    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property.fget
        if fget is None:
            raise AttributeError("unreadable attribute item")
        return fget(self.__instance, key)

class OneStencil:
    def __init__(self, v, nv, num2index):
        self.v = v
        self.nv = nv
        self.num2index = num2index

    @property
    def num(self):
        """
        get the numbering of the velocities
        """
        vectorize = np.vectorize(lambda obj: obj.num)
        return vectorize(self.v)

    @property
    def vx(self):
        """
        get the x component of the velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vx)
        return vectorize(self.v)

    @property
    def vy(self):
        """
        get the y component of the velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vy)
        return vectorize(self.v)

    @property
    def vz(self):
        """
        get the z component of the velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vz)
        return vectorize(self.v)


class Stencil(list):
    """
    A class to define the stencil in velocities of the scheme.
    A specific numbering is used in order to simplify the creation of the schemes.

    Parameters
    ----------
    stencil_dico: a dictionary that contains the following `key:value`

        - 'dim': dim where dim is the value of the spatial dimension (1, 2 or 3)
        - 'number_of_schemes': nscheme where nscheme is the value of the number of used elementary schemes
        - 0: dico0, 1: dico1, ..., (nscheme-1): dico(nscheme-1) where k: dicok contains the velocities of the kth stencil
          (dicok['velocities'] is the list of the velocity indices for the kth stencil)

    Attributes
    ----------
    dim       : the spatial dimension (1, 2 or 3)
    unvtot    : the number of unique velocities involved in the stencils
    vmax      : the maximal velocity in norm for each spatial direction
    vmin      : the minimal velocity in norm for each spatial direction
    nstencils : the number of elementary stencil
    nv        : the number of velocities for each elementary stencil
    uniq_v    : unique velocities used for all stencils
    v         : velocities for each elementary stencil
    v_index   : ???

    Methods
    -------


        .. image:: /images/Velocities_1D.jpeg

        .. image:: /images/Velocities_2D.jpeg

    Examples
    --------

    >>> s = Stencil({'dim': 1,
                     'number_of_schemes': 1,
                     0:{'velocities': range(9)}
                     })
    >>> s
    Stencil informations
             * spatial dimension: dim=1
             * maximal velocity in each direction: [4 None None]
             * Informations for each elementary stencil:
                    stencil 0
                     - number of velocities: 9
                     - velocities: (0: 0), (1: 1), (2: -1), (3: 2), (4: -2), (5: 3), (6: -3), (7: 4), (8: -4),
    >>> s = Stencil({'dim': 2,
                     'number_of_schemes': 2,
                     0:{'velocities': range(9)},
                     1:{'velocities': range(50)}
                     })
    >>> s
    Stencil informations
             * spatial dimension: 2
             * maximal velocity in each direction: [4 3 None]
             * Informations for each elementary stencil:
                    stencil 0
                     - number of velocities: 9
                     - velocities: (0: 0, 0), (1: 1, 0), (2: 0, 1), (3: -1, 0), (4: 0, -1), (5: 1, 1), (6: -1, 1), (7: -1, -1), (8: 1, -1),
                    stencil 1
                     - number of velocities: 50
                     - velocities: (0: 0, 0), (1: 1, 0), (2: 0, 1), (3: -1, 0), (4: 0, -1), (5: 1, 1), (6: -1, 1), (7: -1, -1), (8: 1, -1), (9: 2, 0), (10: 0, 2), (11: -2, 0), (12: 0, -2), (13: 2, 2), (14: -2, 2), (15: -2, -2), (16: 2, -2), (17: 2, 1), (18: 1, 2), (19: -1, 2), (20: -2, 1), (21: -2, -1), (22: -1, -2), (23: 1, -2), (24: 2, -1), (25: 3, 0), (26: 0, 3), (27: -3, 0), (28: 0, -3), (29: 3, 3), (30: -3, 3), (31: -3, -3), (32: 3, -3), (33: 3, 1), (34: 1, 3), (35: -1, 3), (36: -3, 1), (37: -3, -1), (38: -1, -3), (39: 1, -3), (40: 3, -1), (41: 3, 2), (42: 2, 3), (43: -2, 3), (44: -3, 2), (45: -3, -2), (46: -2, -3), (47: 2, -3), (48: 3, -2), (49: 4, 0),

    get the x component of the unique velocities

    >>> s.uvx
    array([ 0,  1,  0, -1,  0,  1, -1, -1,  1,  2,  0, -2,  0,  2, -2, -2,  2,
            2,  1, -1, -2, -2, -1,  1,  2,  3,  0, -3,  0,  3, -3, -3,  3,  3,
            1, -1, -3, -3, -1,  1,  3,  3,  2, -2, -3, -3, -2,  2,  3,  4])

    get the y component of the velocity for the second stencil

    >>> s.vy[1]
    array([ 0,  0,  1,  0, -1,  1,  1, -1, -1,  0,  2,  0, -2,  2,  2, -2, -2,
            1,  2,  2,  1, -1, -2, -2, -1,  0,  3,  0, -3,  3,  3, -3, -3,  1,
            3,  3,  1, -1, -3, -3, -1,  2,  3,  3,  2, -2, -3, -3, -2,  0])
    """
    def __init__(self, dico):
        super(Stencil, self).__init__()
        # get the dimension of the stencil (given in the dictionnary or computed through the geometrical box)
        self.dim = dico.get('dim',None)
        if self.dim is None:
            try:
                boite = dico['box']
                boitex = boite['x']
                boitey = boite.get('y',None)
                boitez = boite.get('z',None)
                self.dim = 1
                if boitey is not None:
                    self.dim += 1
                if boitez is not None:
                    self.dim += 1
            except:
                logging.critical('Error in the creation of the stencil: the spatial dimension cannot be determined')
                sys.exit()

        # get the number of stencils (equal to the number of schemes)
        kkk = 0
        dummy = dico.get(kkk,None)
        while dummy is not None:
            kkk += 1
            dummy = dico.get(kkk,None)
        self.nstencils = kkk

        # get the list of the velocities of each stencil
        v_index = [np.asarray(dico[k]['velocities']) for k in xrange(self.nstencils)]

        # get the unique velocities involved in the stencil
        unique_indices = np.empty(0, dtype=np.int32)
        for vi in v_index:
            unique_indices = np.union1d(unique_indices, vi)

        self.unique_velocities = np.asarray([Velocity(dim=self.dim, num=i) for i in unique_indices])
        self.unvtot = len(self.unique_velocities)

        self.v = []
        self.nv = []
        self.nv_ptr = [0]
        num = self.unum
        for vi in v_index:
            ypos = np.searchsorted(num, vi)
            self.v.append(self.unique_velocities[ypos])
            lvi = len(vi)
            self.nv.append(lvi)
            self.nv_ptr.append(self.nv_ptr[-1] + lvi)

        # get the box where all the schemes are included
        self.vmax = np.max([self.uvx, self.uvy, self.uvz], axis=1)
        self.vmin = np.min([self.uvx, self.uvy, self.uvz], axis=1)

        # get the index in the v[k] of the num velocity
        self.num2index = []
        for k in xrange(self.nstencils):
            num = self.num[k]
            nmax = np.max(num)
            #tmp = np.nan*np.zeros(nmax + 1, dtype=np.int32)
            tmp = 1000 + np.zeros(nmax + 1, dtype=np.int32)
            tmp[num] = xrange(num.size)
            self.num2index.append(tmp)

        # get the index in the v[k] of the num velocity (unique)
        unum = self.unum
        self.unum2index = 1000 + np.zeros(np.max(unum) + 1, dtype=np.int32)
        self.unum2index[unum] = range(unum.size)

        for k in xrange(self.nstencils):
            self.append(OneStencil(self.v[k], self.nv[k], self.num2index[k]))

    @property
    def uvx(self):
        """
        get the x component of the unique velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vx)
        return vectorize(self.unique_velocities)

    @utils.itemproperty
    def vx(self, k):
        """
        get the x component of the velocities for the stencil k
        """
        vectorize = np.vectorize(lambda obj: obj.vx)
        return vectorize(self.v[k])

    @property
    def uvy(self):
        """
        get the y component of the unique velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vy)
        return vectorize(self.unique_velocities)

    @utils.itemproperty
    def vy(self, k):
        """
        get the y component of the velocities for the stencil k
        """
        vectorize = np.vectorize(lambda obj: obj.vy)
        return vectorize(self.v[k])

    @property
    def uvz(self):
        """
        get the z component of the unique velocities
        """
        vectorize = np.vectorize(lambda obj: obj.vz)
        return vectorize(self.unique_velocities)

    @utils.itemproperty
    def vz(self, k):
        """
        get the z component of the velocities for the stencil k
        """
        vectorize = np.vectorize(lambda obj: obj.vz)
        return vectorize(self.v[k])

    @property
    def unum(self):
        """
        get the numbering of the unique velocities
        """
        vectorize = np.vectorize(lambda obj: obj.num)
        return vectorize(self.unique_velocities)

    @utils.itemproperty
    def num(self, k):
        """
        get the numbering of the velocities for the stencil k
        """
        vectorize = np.vectorize(lambda obj: obj.num)
        return vectorize(self.v[k])

    def __str__(self):
        s = "Stencil informations\n"
        s += "\t * spatial dimension: {0:1d}\n".format(self.dim)
        s += "\t * maximal velocity in each direction: "
        s += str(self.vmax)
        s += "\n\t * minimal velocity in each direction: "
        s += str(self.vmin)
        s += "\n\t * Informations for each elementary stencil:\n"
        for k in xrange(self.nstencils):
            s += "\t\tstencil {0:1d}\n".format(k)
            s += "\t\t - number of velocities: {0:2d}\n".format(self.nv[k])
            s += "\t\t - velocities: "
            for v in self.v[k]:
                s += v.__str__() + ', '
            s += '\n'
        return s

    def __repr__(self):
        return self.__str__()

    def visualize(self, viewer, k=None, unique_velocities=False):
        """
        plot the velocities

        Parameters
        ----------
        viewer : package used to plot the figure (could be matplotlib, vtk, ...)
            see viewer for more information
        k : list of stencil index to plot
            if None plot all stencils
        unique_velocities : if True plot the unique velocities

        """
        if self.dim == 3 and not viewer.is3d:
            raise ValueError("viewer doesn't support 3D visualization")

        xmin = xmax = 0
        ymin = ymax = 0
        zmin = zmax = 0

        vectorize = np.vectorize(lambda txt, vx, vy, vz: viewer.add_text(txt, vx, vy, vz))

        if unique_velocities:
            viewer.figure("unique_velocities")

            vx = self.uvx
            vy = vz = 0
            if self.dim >= 2:
                vy = self.uvy
            if self.dim == 3:
                vz = self.uvz

            vectorize(self.unum, vx, vy, vz)

            xmin, xmax = np.min(vx) - 1, np.max(vx) + 1
            ymin, ymax = np.min(vy) - 1, np.max(vy) + 1
            zmin, zmax = np.min(vz) - 1, np.max(vz) + 1

            viewer.axis(xmin, xmax, ymin, ymax, zmin, zmax)

        else:
            if k is None:
                lv = range(self.nstencils)
            elif isinstance(k, int):
                lv = [k]
            else:
                lv = k

            for i in lv:
                viewer.figure("stencil %d"%i)

                vx = self.vx[i]
                vy = vz = 0
                if self.dim >= 2:
                    vy = self.vy[i]
                if self.dim == 3:
                    vz = self.vz[i]

                vectorize(self.num[i], vx, vy, vz)

                xmin, xmax = np.min(vx) - 1, np.max(vx) + 1
                ymin, ymax = np.min(vy) - 1, np.max(vy) + 1
                zmin, zmax = np.min(vz) - 1, np.max(vz) + 1

                viewer.axis(xmin, xmax, ymin, ymax, zmin, zmax)

        viewer.draw()

if __name__ == '__main__':
    """
    d = {'dim': 3,
         'number_of_schemes': 3,
         0:{'velocities': range(19)},
         1:{'velocities': range(27)},
         2:{'velocities': [5, 39, 2]},
         }

    s = Stencil(d)

    #v = viewer.MatplotlibViewer()
    v = viewer.VtkViewer()

    print s.vx[0]
    print s.vy[0]
    print s.vz[0]

    print s.unum

    s.visualize(v)

    """
    d = {'dim': 2,
         'number_of_schemes': 3,
         0:{'velocities': range(5)},
         1:{'velocities': [0,2,4,5,1]},
         2:{'velocities': range(13)},
         }

    s = Stencil(d)

    #v = viewer.MatplotlibViewer()
    #v = viewer.VtkViewer()

    #for i in xrange(5):
    #    print s.get_index(1, i)

    print s.vx[0]
    print s.vy[0]
    print s.vz[0]

    print s.unum

    #s.visualize(v, k=2)