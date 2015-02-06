class UnitEnum(object):
    """Enumeration-like object, specifying the units of measure for length

    Usage:
        unit = UnitEnum.PIXEL
        unit = UnitEnum.EM
        if unit == UnitEnum.CHARACTER :
            ...
    """
    def __new__(cls, *args, **kwargs):
        raise Exception(u"Don't instantiate. Use like an enum")

    __init__ = __new__

    PIXEL = u'px'
    EM = u'em'
    PERCENT = u'%'
    CHARACTER = u'c'


class TwoDimensionalObject(object):
    """Adds a couple useful methods to its subclasses, nothing fancy.
    """
    @classmethod
    def from_dfxp_attribute(cls, attribute):
        """Instantiate the class from a value of the type "4px" or "5%"
        or any number concatenated with a measuring unit (member of UnitEnum)

        :type attribute: string-like
        """
        horizontal, vertical = unicode(attribute).split(u' ')
        horizontal = Size.from_string(horizontal)
        vertical = Size.from_string(vertical)

        return cls(horizontal, vertical)


class Stretch(TwoDimensionalObject):
    """Used for specifying the extent of a rectangle (hot much it stretches),
    or the padding in a rectangle (how much space should be left empty until
    text can be displayed)
    """
    def __init__(self, horizontal, vertical):
        """Use the .from_xxx methods. They know what's best for you.

        :type horizontal: Size
        :type vertical: Size
        """
        self.horizontal = horizontal
        self.vertical = vertical

    def is_measured_in(self, measure_unit):
        """Whether the stretch is only measured in the provided units

        :param measure_unit: a UnitEnum member
        :return: True/False
        """
        return (
            self.horizontal.unit == measure_unit
            and self.vertical.unit == measure_unit
        )

    def __repr__(self):
        return u'<Stretch ({horizontal}, {vertical})>'.format(
            horizontal=self.horizontal, vertical=self.vertical
        )

    def serialized(self):
        """Returns a tuple of the useful attributes of this object"""
        return (
            None if not self.horizontal else self.horizontal.serialized(),
            None if not self.vertical else self.vertical.serialized()
        )


class Region(object):
    """Represents the spatial coordinates of a rectangle

    Don't instantiate by hand. use Region.from_points or Region.from_extent
    """
    @classmethod
    def from_points(cls, p1, p2):
        """Create a rectangle, knowing 2 points on the plane.
        We assume that p1 is in the upper left (closer to the origin)

        :param p1: Point instance
        :param p2: Point instance
        :return: a Point instance
        """
        inst = cls()
        inst._p1 = p1
        inst._p2 = p2
        return inst

    @classmethod
    def from_extent(cls, stretch, origin):
        """Create a rectangle, knowing its upper left origin, and
        spatial extension

        :param stretch: Stretch instance
        :param origin: Point instance
        :return: a Point instance
        """
        inst = cls()
        inst._stretch = stretch
        inst._origin = origin
        return inst

    @property
    def stretch(self):
        """How wide this rectangle stretches (horizontally and vertically)
        """
        if hasattr(self, '_stretch'):
            return self._stretch
        else:
            return self._p1 - self._p2

    @property
    def origin(self):
        """Out of its 4 points, returns the one closest to the origin
        """
        if hasattr(self, '_origin'):
            return self._origin
        else:
            return Point.align_from_origin(self._p1, self._p2)[0]

    upper_left_point = origin

    @property
    def lower_right_point(self):
        """The point furthest from the origin from the rectangle's 4 points
        """
        if hasattr(self, '_p2'):
            return Point.align_from_origin(self._p1, self._p2)[1]
        else:
            return self.origin.add_extent(self.stretch)


class Point(TwoDimensionalObject):
    """Represent a point in 2d space.
    """
    def __init__(self, x, y):
        """
        :type x: Size
        :type y: Size
        """
        self.x = x
        self.y = y

    def __sub__(self, other):
        """Returns an Stretch object, if the other point's units are compatible
        """
        return Stretch(abs(self.x - other.x), abs(self.y - other.y))

    def add_stretch(self, stretch):
        """Returns another Point instance, whose coordinates are the sum of the
         current Point's, and the Stretch instance's.
        """
        return Point(self.x + stretch.horizontal, self.y + stretch.vertical)

    @classmethod
    def align_from_origin(cls, p1, p2):
        """Returns a tuple of 2 points. The first is closest to the origin
        on both axes than the second.

        If the 2 points fulfill this condition, returns them (ordered), if not,
        creates 2 new points.
        """
        if p1.x <= p2.x and p1.y <= p2.y:
            return p1
        if p1.x >= p2.x and p1.y >= p2.y:
            return p2
        else:
            return (Point(min(p1.x, p2.x), min(p1.y, p2.y)),
                    Point(max(p1.x, p2.x), max(p1.y, p2.y)))

    def __repr__(self):
        return u'<Point ({x}, {y})>'.format(
            x=self.x, y=self.y
        )

    def serialized(self):
        """Returns the "useful" values of this object.
        """
        return (
            None if not self.x else self.x.serialized(),
            None if not self.y else self.y.serialized()
        )


class Size(object):
    """Ties together a number with a unit, to represent a size.

    Use as value objects! (don't change after creation)
    """
    def __init__(self, value, unit):
        """
        :param value: A number (float or int will do)
        :param unit: A UnitEnum member
        """
        self.value = value
        self.unit = unit

    def __sub__(self, other):
        if self.unit == other.unit:
            return Size(self.value - other.value, self.unit)
        else:
            raise ValueError(u"The sizes should have the same measure units.")

    def __abs__(self):
        return Size(abs(self.value), self.unit)

    def __cmp__(self, other):
        if self.unit == other.unit:
            return cmp(self.value, other.value)
        else:
            raise ValueError(u"The sizes should have the same measure units.")

    def __add__(self, other):
        if self.unit == other.unit:
            return Size(self.value + other.value, self.unit)

    @classmethod
    def from_string(cls, string):
        """Given a string of the form "46px" or "5%" etc., returns the proper
        size object

        :param string: a number concatenated to any of the UnitEnum members.
        :return: an instance of Size
        """
        units = [UnitEnum.CHARACTER, UnitEnum.PERCENT, UnitEnum.PIXEL,
                 UnitEnum.EM]

        raw_number = string
        unit = None
        for unit in units:
            if raw_number.endswith(unit):
                raw_number = raw_number.rstrip(unit)
                break

        if unit is not None:
            value = None
            try:
                value = float(raw_number)
                value = int(raw_number)
            except ValueError:
                pass

            if value is None:
                raise ValueError(
                    u"Couldn't recognize the string as a number, or the unit "
                    u"specified is not recognized. Only the {units} units "
                    u"are supported".format(units=units)
                )
            instance = cls(value, unit)
            return instance

    def __repr__(self):
        return u'<Size ({value} {unit})>'.format(
            value=self.value, unit=self.unit
        )

    def serialized(self):
        """Returns the "useful" values of this object"""
        return self.value, self.unit


class Padding(object):
    """Represents padding information. Consists of 4 Size objects, representing
    padding from (in this order): before (up), after (down), start (left) and
    end (right).
    """
    def __init__(self, before=None, after=None, start=None, end=None):
        """
        :type before: Size
        :type after: Size
        :type start: Size
        :type end: Size
        """
        self.before = before
        self.after = after
        self.start = start
        self.end = end

    @classmethod
    def from_dfxp_attribute(cls, attribute):
        """As per the docs, the style attribute can contain 1,2,3 or 4 values.

        If 1 value: apply to all edges
        If 2: first applies to before and after, second to start and end
        If 3: first applies to before, second to start and end, third to after
        If 4: before, end, after, start;

        http://www.w3.org/TR/ttaf1-dfxp/#style-attribute-padding

        :param attribute: a string like object, representing a dfxp attr. value
        :return: a Padding object
        """
        values_list = unicode(attribute).split(u' ')
        sizes = []

        for value in values_list:
            sizes.append(Size.from_string(value))

        if len(sizes) == 1:
            return cls(sizes[0], sizes[0], sizes[0], sizes[0])
        elif len(sizes) == 2:
            return cls(sizes[0], sizes[0], sizes[1], sizes[1])
        elif len(sizes) == 3:
            return cls(sizes[0], sizes[2], sizes[1], sizes[1])
        elif len(sizes) == 4:
            return cls(sizes[0], sizes[2], sizes[3], sizes[1])
        else:
            raise ValueError(u'The provided value "{value}" could not be '
                             u"parsed into the a padding. Check out "
                             u"http://www.w3.org/TR/ttaf1-dfxp/"
                             u"#style-attribute-padding for the definition "
                             u"and examples".format(value=attribute))

    def __repr__(self):
        return (
            u"<Padding (before: {before}, after: {after}, start: {start}, "
            u"end: {end})>".format(
                before=self.before, after=self.after, start=self.start,
                end=self.end
            )
        )

    def serialized(self):
        """Returns a tuple containing the useful values of this object
        """
        return (
            None if not self.before else self.before.serialized(),
            None if not self.after else self.after.serialized(),
            None if not self.start else self.start.serialized(),
            None if not self.end else self.end.serialized()
        )


class Layout(object):
    """Should encapsulate all the information needed to determine (as correctly
    as possible) the layout (positioning) of elements on the screen.

     Inheritance of this property, from the CaptionSet to its children is
     specific for each caption type.
    """
    def __init__(self, origin=None, extent=None, padding=None):
        """
        :type origin: Point
        :type extent: Stretch
        :type padding: Padding
        """
        self.origin = origin
        self.extent = extent
        self.padding = padding

    def __repr__(self):
        return (
            u"<Layout (origin: {origin}, extent: {extent}, "
            u"padding: {padding})>".format(
                origin=self.origin, extent=self.extent, padding=self.padding
            )
        )

    def serialized(self):
        """Returns nested tuple containing the "useful" values of this object
        """
        return (
            None if not self.origin else self.origin.serialized(),
            None if not self.extent else self.extent.serialized(),
            None if not self.padding else self.padding.serialized()
        )