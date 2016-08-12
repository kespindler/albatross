from albatross.http_error import HTTPError
from albatross.status_codes import HTTP_400


def caseless_pairs(seq):
    for k, v in seq:
        yield k.lower(), v


class Immutable:
    def __setitem__(self, k, v):
        raise TypeError('Cannot set item on %s' % self.__class__)

    def update(self, E=None, **F):
        raise TypeError('Cannot update on %s' % self.__class__)


class ImmutableMultiDict(Immutable, dict):
    def __getitem__(self, k):
        if k in self:
            return super(ImmutableMultiDict, self).__getitem__(k)[0]
        raise HTTPError(HTTP_400, 'Must provide parameter \'%s\'.' % k)

    def get(self, k, d=None):
        if k in self:
            return super(ImmutableMultiDict, self).__getitem__(k)[0]
        return d

    def get_all(self, k, d=None):
        if k in self:
            return super(ImmutableMultiDict, self).__getitem__(k)
        return d


class CaselessDict(dict):
    def __init__(self, it=None, **kwargs):
        it = caseless_pairs(it) if it else []
        if kwargs:
            kwargs = {k.lower(): v for k, v in kwargs.items()}
        super(CaselessDict, self).__init__(it, **kwargs)

    def __contains__(self, k):
        return super(CaselessDict, self).__contains__(k.lower())

    def __getitem__(self, k):
        return super(CaselessDict, self).__getitem__(k.lower())

    def __iter__(self):
        for k in super(CaselessDict, self).__iter__():
            yield k.lower()

    def __setitem__(self, k, v):
        super(CaselessDict, self).__setitem__(k.lower(), v)

    def get(self, k, d=None):
        if k in self:
            return super(CaselessDict, self).__getitem__(k.lower())
        return d

    def update(self, other=None, **kwargs):
        updates = {k.lower(): v for k, v in kwargs.items()}
        if other:
            if hasattr(other, 'items'):
                other = other.items()
            updates.update(caseless_pairs(other))
        return super(CaselessDict, self).update(updates)


class ImmutableCaselessDict(Immutable, CaselessDict):
    pass


class ImmutableCaselessMultiDict(ImmutableMultiDict, CaselessDict):
    def __init__(self, it=None, **kwargs):
        it = caseless_pairs(it) if it else []
        if kwargs:
            kwargs = {k.lower(): [v] for k, v in kwargs.items()}
        for k, v in it:
            if k in kwargs:
                kwargs[k].append(v)
            else:
                kwargs[k] = [v]
        super(ImmutableCaselessMultiDict, self).__init__(**kwargs)
