from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from .core import AVBPropertyDef, AVBRefList
from . import utils
from . import mobid
from . utils import peek_data
from .interpolation import integrate_iter, lerp, cubic_interpolate, bezier_interpolate

class Component(core.AVBObject):
    class_id = b'COMP'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('left_bob',      '__OMFI:CPNT:LeftBob',    'reference', None),
        AVBPropertyDef('right_bob',     '__OMFI:CPNT:RightBob',   'reference', None),
        AVBPropertyDef('media_kind_id', 'OMFI:CPNT:TrackKind',    'int16',        0),
        AVBPropertyDef('edit_rate',     'EdRate',                 'fexp10',      25),
        AVBPropertyDef('name',          'OMFI:CPNT:Name',         'string',    None),
        AVBPropertyDef('effect_id',     'OMFI:CPNT:EffectID',     'string',    None),
        AVBPropertyDef('attributes',    'OMFI:CPNT:Attributes',   'reference'),
        AVBPropertyDef('session_attrs', 'OMFI:CPNT:SessionAttrs', 'reference', None),
        AVBPropertyDef('precomputed',   'OMFI:CPNT:Precomputed',  'reference', None),
        AVBPropertyDef('param_list',    'OMFI:CPNT:ParamList',    'reference'),
    ]
    __slots__ = ()

    def __init__(self, edit_rate=25, media_kind=None):
        super(Component, self).__init__(self)
        self.attributes = self.root.create.Attributes()
        self.media_kind = media_kind
        self.edit_rate = edit_rate

    def read(self, f):
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        # bob == bytes of binary or bag of bits?
        self.left_bob  = ctx.read_object_ref(self.root, f)
        self.right_bob = ctx.read_object_ref(self.root, f)

        self.media_kind_id = ctx.read_s16(f)
        self.edit_rate = ctx.read_exp10_encoded_float(f)
        self.name = ctx.read_string(f) or None
        self.effect_id = ctx.read_string(f) or None

        self.attributes = ctx.read_object_ref(self.root, f)
        self.session_attrs = ctx.read_object_ref(self.root, f)

        self.precomputed = ctx.read_object_ref(self.root, f)

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 72)
                self.param_list = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

    def write(self, f):
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)
        ctx.write_object_ref(self.root, f, self.left_bob)
        ctx.write_object_ref(self.root, f, self.right_bob)
        ctx.write_s16(f, self.media_kind_id)

        ctx.write_exp10_encoded_float(f, self.edit_rate)

        if self.name:
            ctx.write_string(f, self.name)
        else:
            ctx.write_u16(f, 0xFFFF)

        if self.effect_id:
            ctx.write_string(f, self.effect_id)
        else:
            ctx.write_u16(f, 0xFFFF)

        ctx.write_object_ref(self.root, f, self.attributes)
        ctx.write_object_ref(self.root, f, self.session_attrs)
        ctx.write_object_ref(self.root, f, self.precomputed)

        if hasattr(self, 'param_list'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.param_list)

    @property
    def media_kind(self):
        if self.media_kind_id == 0:
            return None
        elif self.media_kind_id == 1:
            return "picture"
        elif self.media_kind_id == 2:
            return "sound"
        elif self.media_kind_id == 3:
            return "timecode"
        elif self.media_kind_id == 4:
            return "edgecode"
        elif self.media_kind_id == 5:
            return "attribute"
        elif self.media_kind_id == 6:
            return 'effectdata'
        elif self.media_kind_id == 7:
            return 'DescriptiveMetadata'
        elif self.media_kind_id == 16:
            return "DataEssenceTrack"
        else:
            return "unknown%d" % self.media_kind_id

    @media_kind.setter
    def media_kind(self, value):
        if value == None:
            self.media_kind_id = 0
        elif value == "picture":
            self.media_kind_id = 1
        elif value == "sound":
            self.media_kind_id = 2
        elif value =="timecode":
            self.media_kind_id = 3
        elif value == "edgecode":
            self.media_kind_id = 4
        elif value == "attribute":
            self.media_kind_id = 5
        elif value == 'effectdata':
            self.media_kind_id = 6
        elif value == 'DescriptiveMetadata':
            self.media_kind_id = 7
        elif value == 'DataEssenceTrack':
            self.media_kind_id = 16
        else:
            raise ValueError('unknown media kind: %s' % str(value))

@utils.register_class
class Sequence(Component):
    class_id = b"SEQU"
    propertydefs_dict = {}
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('components', 'OMFI:SEQU:Sequence', 'ref_list'),
    ]
    __slots__ = ()

    def __init__(self, edit_rate=25, media_kind=None):
        super(Sequence, self).__init__(edit_rate=edit_rate, media_kind=media_kind)
        self.components = []

    def read(self, f):
        super(Sequence, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        count = ctx.read_u32(f)
        self.components = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            # print ref
            self.components.append(ref)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Sequence, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_u32(f, len(self.components))
        for c in self.components:
            ctx.write_object_ref(self.root, f, c)

        ctx.write_u8(f, 0x03)

    @property
    def length(self):
        length = 0
        for component in self.components:
            if component.class_id == b'TNFX':
                length -= component.length
            else:
                length += component.length
        return length

    def nearest_component_at_time(self, edit_unit):
        """ returns the nearest component to edit_unit and its start position"""
        index, position = self.nearest_index_at_time(edit_unit)
        return self.components[index], position

    def nearest_index_at_time(self, edit_unit):
        """returns the index of the nearest component to edit_unit and its start position"""
        last_component = None
        last_index = 0
        last_pos = 0

        # this needs to go past target index to handle Transitions
        for index, position, component in self.positions():

            # skip zero length FILL components
            if component.length == 0:
                continue

            if component.class_id == b'TNFX':
                if position <= edit_unit < position + component.length:
                    return index, position

            # gone past return previous
            if last_component and position >= edit_unit:
                return last_index, last_pos

            last_component = component
            last_index = index
            last_pos = position

        return last_index, last_pos

    def positions(self):
        length = 0
        for index, component in enumerate(self.components):

            if component.class_id == b'TNFX':
                length -= component.length
                yield (index, length, component)
            else:
                yield (index, length, component)
                length += component.length


class Clip(Component):
    class_id = b'CLIP'
    propertydefs_dict = {}
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('length', 'OMFI:CLIP:Length', 'int32', 0),
    ]
    __slots__ = ()

    def read(self, f):
        super(Clip, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)
        self.length = ctx.read_u32(f)

    def write(self, f):
        super(Clip, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)
        ctx.write_u32(f, self.length)

@utils.register_class
class SourceClip(Clip):
    class_id = b'SCLP'
    propertydefs_dict = {}
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('track_id',   'OMFI:SCLP:SourceTrack',     'int16', 0),
        AVBPropertyDef('start_time', 'OMFI:SCLP:SourcePosition',  'int32', 0),
        AVBPropertyDef('mob_id',     'MobID',                     'MobID'),
    ]
    __slots__ = ()

    def __init__(self, edit_rate=25, media_kind=None):
        super(SourceClip, self).__init__(edit_rate=edit_rate, media_kind=media_kind)
        self.mob_id = mobid.MobID()

    def read(self, f):
        super(SourceClip, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        mob_id_hi = ctx.read_u32(f)
        mob_id_lo = ctx.read_u32(f)

        self.track_id = ctx.read_s16(f)
        self.start_time = ctx.read_s32(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                self.mob_id = ctx.read_mob_id(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(SourceClip, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        lo = self.mob_id.material.time_low
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)

        ctx.write_u32(f, lo)
        ctx.write_u32(f, hi)

        ctx.write_s16(f, self.track_id)
        ctx.write_s32(f, self.start_time)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_mob_id(f, self.mob_id)

        ctx.write_u8(f, 0x03)

    @property
    def mob(self):
        if hasattr(self, 'mob_id'):
            mob_id = self.mob_id
            if mob_id:
                return self.root.content.mob_dict.get(self.mob_id, None)

    @property
    def track(self):
        mob = self.mob
        if mob:
            for track in mob.tracks:
                if track.index == self.track_id and track.component and self.media_kind == track.component.media_kind:
                    return track

@utils.register_class
class Timecode(Clip):
    class_id = b'TCCP'
    propertydefs_dict = {}
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('flags', 'OMFI:TCCP:Flags',   'int32',  0),
        AVBPropertyDef('fps',   'OMFI:TCCP:FPS',     'int32', 25),
        AVBPropertyDef('start', 'OMFI:TCCP:StartTC', 'int32',  0),
    ]
    __slots__ = ()

    def read(self, f):
        super(Timecode, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        # drop ??
        self.flags = ctx.read_u32(f)
        self.fps = ctx.read_u16(f)

        # unused
        f.read(6)

        self.start = ctx.read_u32(f)
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Timecode, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u32(f, self.flags)
        ctx.write_u16(f, self.fps)
        f.write(bytearray(6))
        ctx.write_u32(f, self.start)

        ctx.write_u8(f, 0x03)

@utils.register_class
class Edgecode(Clip):
    class_id = b'ECCP'
    propertydefs_dict = {}
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('header',      'OMFI:ECCP:Header',      'bytes'),
        AVBPropertyDef('film_kind',   'OMFI:ECCP:FilmKind',   'uint8'),
        AVBPropertyDef('code_format', 'OMFI:ECCP:CodeFormat', 'uint8'),
        AVBPropertyDef('base_perf',   'OMFI:ECCP:BasePerf',   'uint16'),
        AVBPropertyDef('start_ec',    'OMFI:ECCP:StartEC',    'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Edgecode, self).read(f)
        ctx = self.root.ictx

        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.header = bytearray(f.read(8))
        self.film_kind = ctx.read_u8(f)
        self.code_format =  ctx.read_u8(f)
        self.base_perf = ctx.read_u16(f)
        unused_a  = ctx.read_u32(f)
        self.start_ec = ctx.read_s32(f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Edgecode, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        assert len(self.header) == 8
        f.write(self.header)
        ctx.write_u8(f, self.film_kind)
        ctx.write_u8(f, self.code_format)
        ctx.write_u16(f, self.base_perf)
        #unused
        ctx.write_u32(f, 0)
        ctx.write_s32(f, self.start_ec)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TrackRef(Clip):
    class_id = b'TRKR'
    propertydefs_dict = {}
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('relative_scope', 'OMFI:TRKR:RelativeScope', 'int16',  0),
        AVBPropertyDef('relative_track', 'OMFI:TRKR:RelativeTrack', 'int16', -1),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackRef, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.relative_scope = ctx.read_s16(f)
        self.relative_track = ctx.read_s16(f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackRef, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, self.relative_scope)
        ctx.write_s16(f, self.relative_track)

        ctx.write_u8(f, 0x03)


CP_TYPE_INT = 1
CP_TYPE_DOUBLE = 2
CP_TYPE_REFERENCE = 4

INTERPOLATION_MAP = {
    2: 'ConstantInterp',
    3: 'LinearInterp',
    5: 'BezierInterpolator',
    6: 'CubicInterpolator',
}

POINT_PROPERTY_MAP = {
    5: 'PP_IN_TANGENT_POS_U',
    6: 'PP_IN_TANGENT_VAL_U',
    7: 'PP_OUT_TANGENT_POS_U',
    8: 'PP_OUT_TANGENT_VAL_U',
    9: 'PP_TANGENT_MODE_U',
    14: 'PP_BASE_FRAME_U',
}

@utils.register_helper_class
class ParamControlPoint(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('offset',    'OMFI:PRCL:Offset',     'rational'),
        AVBPropertyDef('timescale', 'OMFI:PRCL:TimeScale',  'int32'),
        AVBPropertyDef('value',     'OMFI:PRCL:Value',      'number'), # int or double
        AVBPropertyDef('pp',        'OMFI:PRCL:PP',         'list'),
    ]
    __slots__ = ()

    @property
    def time(self):
        num = float(self.offset[0])
        den = float(self.offset[1])
        if den == 0.0:
            raise ValueError("bad denominator")

        # TODO: check if this is what timescale does
        if self.timescale == 0:
            raise ValueError("bad timescale")

        return num / den * self.timescale

    @property
    def point_properties(self):
        props = {}
        for p in self.pp:
            name = p.name
            if name:
                props[p.name] = p.value
        return props

    @property
    def base_frame(self):
        for p in self.pp:
            if p.name == 'PP_BASE_FRAME_U':
                return p.value
        return 0

    @property
    def tangents(self):
        props = self.point_properties
        return [(float(props.get("PP_IN_TANGENT_POS_U", 0)),
                 float(props.get("PP_IN_TANGENT_VAL_U", 0))),
                (float(props.get("PP_OUT_TANGENT_POS_U", 0)),
                 float(props.get("PP_OUT_TANGENT_VAL_U", 0)))]


@utils.register_helper_class
class ParamControlPointProperty(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('code',  'OMFI:PRCL:PPCode',  'int16'),
        AVBPropertyDef('type',  'OMFI:PRCL:PPType',  'int16'),
        AVBPropertyDef('value', 'OMFI:PRCL:PPValue', 'number'), # int or double
    ]
    __slots__ = ()

    @property
    def name(self):
        return POINT_PROPERTY_MAP.get(self.code, None)

    @property
    def type_name(self):
        if self.type == CP_TYPE_INT:
            return 'int'
        elif self.type == CP_TYPE_DOUBLE:
            return 'double'
        elif self.type == CP_TYPE_REFERENCE:
            return 'reference'
        else:
            return 'unknown'


@utils.register_class
class ParamClip(Clip):
    propertydefs_dict = {}
    class_id = b'PRCL'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('interp_kind',    'OMFI:PRCL:InterpKind',    'int32'),
        AVBPropertyDef('value_type',     'OMFI:PRCL:ValueType',     'int16'),
        AVBPropertyDef('extrap_kind',    'OMFI:PCRL:ExtrapKind',    'int32'),
        AVBPropertyDef('control_points', 'OMFI:PRCL:ControlPoints', 'list'),
        AVBPropertyDef('fields',         'OMFI:PRCL:Fields',        'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ParamClip, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.interp_kind = ctx.read_s32(f)
        self.value_type = ctx.read_s16(f)

        assert self.value_type in (CP_TYPE_INT, CP_TYPE_DOUBLE, CP_TYPE_REFERENCE)

        point_count = ctx.read_s32(f)
        assert point_count >= 0

        self.control_points = []
        for i in range(point_count):
            cp = ParamControlPoint.__new__(ParamControlPoint, root=self.root)
            num = ctx.read_s32(f)
            den = ctx.read_s32(f)
            cp.offset = [num, den]
            cp.timescale = ctx.read_s32(f)

            if self.value_type == CP_TYPE_INT:
                cp.value = ctx.read_s32(f)
            elif self.value_type == CP_TYPE_DOUBLE:
                cp.value = ctx.read_double(f)
            elif self.value_type == CP_TYPE_REFERENCE:
                cp.value = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("unknown value type: %d" % self.value_type)

            pp_count = ctx.read_s16(f)
            assert pp_count >= 0
            cp.pp = []
            for j in range(pp_count):
                pp = ParamControlPointProperty.__new__(ParamControlPointProperty, root=self.root)
                pp.code = ctx.read_s16(f)
                pp.type = ctx.read_s16(f)

                if pp.type == CP_TYPE_DOUBLE:
                    pp.value = ctx.read_double(f)
                elif pp.type == CP_TYPE_INT:
                    pp.value  = ctx.read_s32(f)
                else:
                    raise ValueError("unknown PP type: %d" % pp.type)

                cp.pp.append(pp)

            self.control_points.append(cp)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.extrap_kind = ctx.read_s32(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 71)
                self.fields = ctx.read_s32(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(ParamClip, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.interp_kind)
        ctx.write_s16(f, self.value_type)

        ctx.write_s32(f, len(self.control_points))

        for cp in self.control_points:
            ctx.write_s32(f, cp.offset[0])
            ctx.write_s32(f, cp.offset[1])
            ctx.write_s32(f, cp.timescale)

            if self.value_type == CP_TYPE_INT:
                ctx.write_s32(f, cp.value)
            elif self.value_type == CP_TYPE_DOUBLE:
                ctx.write_double(f, cp.value)
            elif self.value_type == CP_TYPE_REFERENCE:
                ctx.write_object_ref(self.root, f, cp.value)
            else:
                raise ValueError("unknown value type: %d" % cp.value_type)

            ctx.write_s16(f, len(cp.pp))
            for pp in cp.pp:

                ctx.write_s16(f, pp.code)
                ctx.write_s16(f, pp.type)

                if pp.type == CP_TYPE_DOUBLE:
                    ctx.write_double(f, pp.value)
                elif pp.type == CP_TYPE_INT:
                    ctx.write_s32(f, pp.value)
                else:
                    raise ValueError("unknown PP type: %d" % pp.type)

        if hasattr(self, 'extrap_kind'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.extrap_kind)

        if hasattr(self, 'fields'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.fields)

        ctx.write_u8(f, 0x03)

    @property
    def value_type_name(self):
        if self.value_type == CP_TYPE_INT:
            return 'int'
        elif self.value_type == CP_TYPE_DOUBLE:
            return 'double'
        elif self.value_type == CP_TYPE_REFERENCE:
            return 'reference'
        else:
            return 'unknown'

    @property
    def interp(self):
        return INTERPOLATION_MAP.get(self.interp_kind, 'unknown')

    def nearest_index(self, t):
        """
        binary search for index of point.time <= t
        """
        if not self.control_points:
            raise ValueError("ParamClip has no control points")

        start = 0
        end = len(self.control_points) - 1
        while True:
            if end < start:
                return max(0, end)

            m = (start + end) // 2
            p = self.control_points[m]
            if p.time < t:
                start = m + 1
            elif p.time > t:
                end = m - 1
            else:
                return m


    def value_at(self, time):
        if not self.control_points:
            raise ValueError("ParamClip has no control points")
        t = float(time)
        index = self.nearest_index(t)
        p1 = self.control_points[index]

        # clamp if t outside of range
        if t < p1.time or index + 1 >= len(self.control_points):
            return float(p1.value)

        if self.interp == 'ConstantInterp':
            return float(p1.value)

        p2 = self.control_points[index+1]

        if self.interp == 'LinearInterp':
            t_len = float(p2.time) - float(p1.time)
            t_diff = t - float(p1.time)
            t_mix = t_diff/t_len

            v0 = float(p1.value)
            v1 = float(p2.value)
            return lerp(v0, v1, t_mix)

        elif self.interp == 'BezierInterpolator':
            t0 = float(p1.time)
            v0 = float(p1.value)

            t3 = float(p2.time)
            v3 = float(p2.value)

            tangents = p1.tangents[1]
            t1 = t0 + tangents[0]
            v1 = v0 + tangents[1]

            tangents = p2.tangents[0]
            t2 = t3 + tangents[0]
            v2 = v3 + tangents[1]

            return bezier_interpolate((t0, v0),
                                      (t1, v1),
                                      (t2, v2),
                                      (t3, v3), t)

        elif self.interp == 'CubicInterpolator':
            t1 = float(p1.time)
            v1 = float(p1.value)

            t2 = float(p2.time)
            v2 = float(p2.value)

            if index - 1 >= 0:
                p0 = self.control_points[index - 1]
                t0 = float(p0.time)
                v0 = float(p0.value)
            else:
                t0 = t1 - ((t2 - t1) * 0.5)
                v0 = v1

            if index + 2 < len(self.control_points):
                p3 = self.control_points[index + 2]
                t3 = float(p3.time)
                v3 = float(p3.value)
            else:
                t3 = t2 + ((t2 - t1) * 0.5)
                v3 = v2

            return cubic_interpolate((t0, v0),
                                     (t1, v1),
                                     (t2, v2),
                                     (t3, v3), t)

        else:
            raise NotImplementedError("Interpolation not implemented for %s %s" %
                           (self.interp, str(self.interp_kind)))

        return 0.0

    def integrate(self, start, end=None):
        # first speed map key frame is the zero point
        # of the offset map curve
        first = self.control_points[0]
        center = int(first.time)
        if end is None:
            last = self.control_points[-1]
            end = int(last.time)

        if start > end:
            raise ValueError("start needs to be less then end")

        time = []
        value = []
        offset_index = None

        inter_start = min(start, center)
        inter_end = max(center,  end+1)

        for i, (t,v) in enumerate(integrate_iter(self.value_at, inter_start, inter_end)):
            time.append(t)
            value.append(v)

            if t == center:
                offset_index = i

        center_offset = value[offset_index]

        # not really sure what this base frame offset is about
        # but appears to contain the how much calculation is off...
        center_offset -= first.base_frame

        result = []
        for i, t in enumerate(time):
            if t > end:
                break

            if t >= start:
                v = value[i] - center_offset
                result.append((t, v))

        return result

@utils.register_helper_class
class ControlPoint(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('offset',     'OMFI:CTRL:Offset',    'rational'),
        AVBPropertyDef('time_scale', 'OMFI:CTRL:TimeScale', 'int32'),
        AVBPropertyDef('value',      'OMFI:CTRL:Value',     'bool'),
        AVBPropertyDef('pp',         'OMFI:CTRL:PP',        'list'),
    ]
    __slots__ = ()

@utils.register_helper_class
class ControlPointProperty(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('code',    'OMFI:CTRL:PPCode',  'int16'),
        AVBPropertyDef('value',   'OMFI:CTRL:PP',      'rational'),
    ]
    __slots__ = ()


@utils.register_class
class ControlClip(Clip):
    propertydefs_dict = {}
    class_id = b'CTRL'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('interp_kind',    'OMFI:CTRL:InterpKin',    'int32'),
        AVBPropertyDef('control_points', 'OMFI:CTRL:ControlPoints', 'list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ControlClip, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        self.interp_kind = ctx.read_s32(f)
        count = ctx.read_s32(f)
        self.control_points = []
        # print(self.interp_kind, count)
        #
        # print(peek_data(f).encode("hex"))
        for i in range(count):
            cp = ControlPoint.__new__(ControlPoint, root=self.root)
            a = ctx.read_s32(f)
            b = ctx.read_s32(f)
            cp.offset = [a, b]
            cp.time_scale = ctx.read_s32(f)

            # TODO: find sample with this False
            has_value = ctx.read_bool(f)
            assert has_value == True

            a = ctx.read_s32(f)
            b = ctx.read_s32(f)
            cp.value = [a, b]
            cp.pp = []

            pp_count = ctx.read_s16(f)
            assert pp_count >= 0
            for j in range(pp_count):
                pp = ControlPointProperty.__new__(ControlPointProperty, root=self.root)
                pp.code = ctx.read_s16(f)
                a = ctx.read_s32(f)
                b = ctx.read_s32(f)
                pp.value = [a,b]
                cp.pp.append(pp)

            self.control_points.append(cp)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(ControlClip, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_s32(f, self.interp_kind)

        ctx.write_s32(f, len(self.control_points))
        for cp in self.control_points:
            ctx.write_s32(f, cp.offset[0])
            ctx.write_s32(f, cp.offset[1])
            ctx.write_s32(f, cp.time_scale)

            ctx.write_bool(f, True)
            ctx.write_s32(f, cp.value[0])
            ctx.write_s32(f, cp.value[1])

            ctx.write_s16(f, len(cp.pp))
            for pp in cp.pp:
                ctx.write_s16(f, pp.code)
                ctx.write_s32(f, pp.value[0])
                ctx.write_s32(f, pp.value[1])

        ctx.write_u8(f, 0x03)

@utils.register_class
class Filler(Clip):
    propertydefs_dict = {}
    class_id = b'FILL'
    __slots__ = ()

    def read(self, f):
        super(Filler, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Filler, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u8(f, 0x03)
