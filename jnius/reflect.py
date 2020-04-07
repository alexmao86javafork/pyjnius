from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
__all__ = ('autoclass', 'ensureclass')
from six import with_metaclass
import logging

from .jnius import (
    JavaClass, MetaJavaClass, JavaMethod, JavaStaticMethod,
    JavaField, JavaStaticField, JavaMultipleMethod, find_javaclass,
    JavaException
)

log = logging.getLogger(__name__)
from collections import defaultdict


class Class(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/Class'

    desiredAssertionStatus = JavaMethod('()Z')
    forName = JavaMultipleMethod([
        ('(Ljava/lang/String,Z,Ljava/lang/ClassLoader;)Ljava/langClass;', True, False),
        ('(Ljava/lang/String;)Ljava/lang/Class;', True, False), ])
    getClassLoader = JavaMethod('()Ljava/lang/ClassLoader;')
    getClasses = JavaMethod('()[Ljava/lang/Class;')
    getComponentType = JavaMethod('()Ljava/lang/Class;')
    getConstructor = JavaMethod('([Ljava/lang/Class;)Ljava/lang/reflect/Constructor;')
    getConstructors = JavaMethod('()[Ljava/lang/reflect/Constructor;')
    getDeclaredClasses = JavaMethod('()[Ljava/lang/Class;')
    getDeclaredConstructor = JavaMethod('([Ljava/lang/Class;)Ljava/lang/reflect/Constructor;')
    getDeclaredConstructors = JavaMethod('()[Ljava/lang/reflect/Constructor;')
    getDeclaredField = JavaMethod('(Ljava/lang/String;)Ljava/lang/reflect/Field;')
    getDeclaredFields = JavaMethod('()[Ljava/lang/reflect/Field;')
    getDeclaredMethod = JavaMethod('(Ljava/lang/String,[Ljava/lang/Class;)Ljava/lang/reflect/Method;')
    getDeclaredMethods = JavaMethod('()[Ljava/lang/reflect/Method;')
    getDeclaringClass = JavaMethod('()Ljava/lang/Class;')
    getField = JavaMethod('(Ljava/lang/String;)Ljava/lang/reflect/Field;')
    getFields = JavaMethod('()[Ljava/lang/reflect/Field;')
    getInterfaces = JavaMethod('()[Ljava/lang/Class;')
    getMethod = JavaMethod('(Ljava/lang/String,[Ljava/lang/Class;)Ljava/lang/reflect/Method;')
    getMethods = JavaMethod('()[Ljava/lang/reflect/Method;')
    getModifiers = JavaMethod('()[I')
    getName = JavaMethod('()Ljava/lang/String;')
    getPackage = JavaMethod('()Ljava/lang/Package;')
    getProtectionDomain = JavaMethod('()Ljava/security/ProtectionDomain;')
    getResource = JavaMethod('(Ljava/lang/String;)Ljava/net/URL;')
    getResourceAsStream = JavaMethod('(Ljava/lang/String;)Ljava/io/InputStream;')
    getSigners = JavaMethod('()[Ljava/lang/Object;')
    getSuperclass = JavaMethod('()Ljava/lang/Class;')
    isArray = JavaMethod('()Z')
    isAssignableFrom = JavaMethod('(Ljava/lang/reflect/Class;)Z')
    isInstance = JavaMethod('(Ljava/lang/Object;)Z')
    isInterface = JavaMethod('()Z')
    isPrimitive = JavaMethod('()Z')
    newInstance = JavaMethod('()Ljava/lang/Object;')
    toString = JavaMethod('()Ljava/lang/String;')

    def __str__(self):
        return (
            '%s: [%s]' if self.isArray() else '%s: %s'
        ) % (
            'Interface' if self.isInterface() else
            'Primitive' if self.isPrimitive() else
            'Class',
            self.getName()
        )

    def __repr__(self):
        return '<%s at 0x%x>' % (self, id(self))


class Object(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/Object'

    getClass = JavaMethod('()Ljava/lang/Class;')
    hashCode = JavaMethod('()I')


class Modifier(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/reflect/Modifier'

    isAbstract = JavaStaticMethod('(I)Z')
    isFinal = JavaStaticMethod('(I)Z')
    isInterface = JavaStaticMethod('(I)Z')
    isNative = JavaStaticMethod('(I)Z')
    isPrivate = JavaStaticMethod('(I)Z')
    isProtected = JavaStaticMethod('(I)Z')
    isPublic = JavaStaticMethod('(I)Z')
    isStatic = JavaStaticMethod('(I)Z')
    isStrict = JavaStaticMethod('(I)Z')
    isSynchronized = JavaStaticMethod('(I)Z')
    isTransient = JavaStaticMethod('(I)Z')
    isVolatile = JavaStaticMethod('(I)Z')


class Method(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/reflect/Method'

    getName = JavaMethod('()Ljava/lang/String;')
    toString = JavaMethod('()Ljava/lang/String;')
    getParameterTypes = JavaMethod('()[Ljava/lang/Class;')
    getReturnType = JavaMethod('()Ljava/lang/Class;')
    getModifiers = JavaMethod('()I')
    isVarArgs = JavaMethod('()Z')


class Field(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/reflect/Field'

    getName = JavaMethod('()Ljava/lang/String;')
    toString = JavaMethod('()Ljava/lang/String;')
    getType = JavaMethod('()Ljava/lang/Class;')
    getModifiers = JavaMethod('()I')


class Constructor(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/reflect/Constructor'

    toString = JavaMethod('()Ljava/lang/String;')
    getParameterTypes = JavaMethod('()[Ljava/lang/Class;')
    getModifiers = JavaMethod('()I')
    isVarArgs = JavaMethod('()Z')


def get_signature(cls_tp):
    tp = cls_tp.getName()
    if tp[0] == '[':
        return tp.replace('.', '/')
    signatures = {
        'void': 'V', 'boolean': 'Z', 'byte': 'B',
        'char': 'C', 'short': 'S', 'int': 'I',
        'long': 'J', 'float': 'F', 'double': 'D'}
    ret = signatures.get(tp)
    if ret:
        return ret
    # don't do it in recursive way for the moment,
    # error on the JNI/android: JNI ERROR (app bug): local reference table
    # overflow (max=512)

    # ensureclass(tp)
    return 'L{0};'.format(tp.replace('.', '/'))


registers = []


def ensureclass(clsname):
    if clsname in registers:
        return
    jniname = clsname.replace('.', '/')
    if MetaJavaClass.get_javaclass(jniname):
        return
    registers.append(clsname)
    autoclass(clsname)


def lower_name(s):
    return s[:1].lower() + s[1:] if s else ''


def bean_getter(s):
    return (s.startswith('get') and len(s) > 3 and s[3].isupper()) or (s.startswith('is') and len(s) > 2 and s[2].isupper())


def log_method(method, name, signature):
    mods = method.getModifiers()
    log.debug(
        '\nmeth: %s\n'
        '  sig: %s\n'
        '  Public %s\n'
        '  Private %s\n'
        '  Protected %s\n'
        '  Static %s\n'
        '  Final %s\n'
        '  Synchronized %s\n'
        '  Volatile %s\n'
        '  Transient %s\n'
        '  Native %s\n'
        '  Interface %s\n'
        '  Abstract %s\n'
        '  Strict %s\n',
        name,
        signature,
        Modifier.isPublic(mods),
        Modifier.isPrivate(mods),
        Modifier.isProtected(mods),
        Modifier.isStatic(mods),
        Modifier.isFinal(mods),
        Modifier.isSynchronized(mods),
        Modifier.isVolatile(mods),
        Modifier.isTransient(mods),
        Modifier.isNative(mods),
        Modifier.isInterface(mods),
        Modifier.isAbstract(mods),
        Modifier.isStrict(mods)
    )

def identifyHierarchy(cls, level, classList, concrete=True):
    classList.append((cls,level))
    supercls = cls.getSuperclass()
    if supercls is not None:
        identifyHierarchy(supercls, level+1, classList, concrete)
    intfcs = cls.getInterfaces()
    if intfcs is not None:
        for intf in intfcs:
            identifyHierarchy(intf, level+1, classList, concrete)
    if not concrete and cls.isInterface() and len(intfcs) ==0:
        classList.append((find_javaclass('java.lang.Object'),level+1))
    #return classList
         


def autoclass(clsname):
    jniname = clsname.replace('.', '/')
    cls = MetaJavaClass.get_javaclass(jniname)
    if cls:
        return cls

    classDict = {}

    # c = Class.forName(clsname)
    c = find_javaclass(clsname)
    if c is None:
        raise Exception('Java class {0} not found'.format(c))
        return None

    constructors = []
    for constructor in c.getConstructors():
        sig = '({0})V'.format(
            ''.join([get_signature(x) for x in constructor.getParameterTypes()]))
        constructors.append((sig, constructor.isVarArgs()))
    classDict['__javaconstructor__'] = constructors

    classHierachy=[]
    identifyHierarchy(c, 0, classHierachy, not c.isInterface())
    classHierachy.reverse()

    print("autoclass(%s) intf %r hierarchy is %s" % (clsname,c.isInterface(),classHierachy))
    clsDone=set()

    clsMethods=defaultdict(list)

    #we now walk the hierarchy, from top of the tree, identifying methods
    #hopefully we start at java.lang.Object 
    for cls,level in classHierachy:
        #dont analyse a given class more than once.
        #many interfaces can lead to java.lang.Object 
        if cls in clsDone:
            continue
        clsDone.add(cls)
        #as we are walking the entire hierarchy, we only need getDeclaredMethods()
        #to get what is in this class; other parts of the hierarchy will be found
        #in those respective classes.
        methods = cls.getDeclaredMethods()
        methods_name = [x.getName() for x in methods]
        for index, method in enumerate(methods):
            name = methods_name[index]
            #print("%s %s" % (str(cls), name))

            clsMethods[name].append((cls, method, level))
    
    #having collated the mthods, identify if there are any with the same name
    for name in clsMethods:        
        if len(clsMethods[name]) == 1:
            #uniquely named method
            owningCls, method, level = clsMethods[name][0]
            static = Modifier.isStatic(method.getModifiers())
            varargs = method.isVarArgs()
            sig = '({0}){1}'.format(
                ''.join([get_signature(x) for x in method.getParameterTypes()]),
                get_signature(method.getReturnType()))
            if log.level <= logging.DEBUG:
                log_method(method, name, sig)
            classDict[name] = (JavaStaticMethod if static else JavaMethod)(sig, varargs=varargs)
            if name != 'getClass' and bean_getter(name) and len(method.getParameterTypes()) == 0:
                lowername = lower_name(name[2 if name.startswith('is') else 3:])
                classDict[lowername] = (lambda n: property(lambda self: getattr(self, n)()))(name)
        else:
            # multiple signatures
            signatures = []
            #print("method with %d multiple signatures is %s in cls %s" % (len(clsMethods[name]), name, c))
            
            
            #assume there can be no more than 10000 levels of inheritance
            paramsig_to_level=defaultdict(lambda: 10000)
            #we now identify if any have the same signature, as we will call the _lowest_, ie min level
            for owningCls, method, level in clsMethods[name]:
                param_sig = ''.join([get_signature(x) for x in method.getParameterTypes()])
                #print("\t owner %s level %d param_sig %s" % (str(owningCls), level, param_sig))
                if level < paramsig_to_level[param_sig]:
                    paramsig_to_level[param_sig] = level

            for owningCls, method, level in clsMethods[name]:
                param_sig = ''.join([get_signature(x) for x in method.getParameterTypes()])
                #only accept the parameter signature at the deepest level of hierarchy (i.e. min level)
                if level > paramsig_to_level[param_sig]:
                    #print("discarding %s name from %s at level %d" % (name, str(owningCls), level))
                    continue

                return_sig = get_signature(method.getReturnType())
                sig = '({0}){1}'.format(param_sig, return_sig)
                
                if log.level <= logging.DEBUG:
                    log_method(method, name, sig)
                signatures.append((sig, Modifier.isStatic(method.getModifiers()), method.isVarArgs()))

            #print("method selected %d multiple signatures of %s" % (len(signatures), str(signatures)))
            classDict[name] = JavaMultipleMethod(signatures)

    def _getitem(self, index):
        try:
            return self.get(index)
        except JavaException as e:
            # initialize the subclass before getting the Class.forName
            # otherwise isInstance does not know of the subclass
            mock_exception_object = autoclass(e.classname)()
            if find_javaclass("java.lang.IndexOutOfBoundsException").isInstance(mock_exception_object):
                # python for...in iteration checks for end of list by waiting for IndexError
                raise IndexError()
            else:
                raise

    for iclass in c.getInterfaces():
        if iclass.getName() == 'java.util.List':
            classDict['__getitem__'] = _getitem
            classDict['__len__'] = lambda self: self.size()
            break

    for field in c.getFields():
        static = Modifier.isStatic(field.getModifiers())
        sig = get_signature(field.getType())
        cls = JavaStaticField if static else JavaField
        classDict[field.getName()] = cls(sig)

    classDict['__javaclass__'] = clsname.replace('.', '/')
    return MetaJavaClass.__new__(
        MetaJavaClass,
        clsname,
        (JavaClass, ),
        classDict)
