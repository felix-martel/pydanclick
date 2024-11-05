# Example: Known Types

By default `pydanclick` recognize `pydantic` types that should be parsed as string:

- [pydantic.SecretStr][]
- [pydantic.SecretBytes][]
- all [pydantic_core.Url][] and [pydantic_core.MultiHostUrl][] (ex: [pydantic.HttpUrl][])
- [pydantic.NameEmail][]
- [pydantic.networks.EmailStr][]
- [pydantic.networks.IPvAnyAddress][] and [ipaddress.IPv4Address][]/[ipaddress.IPv6Address][]
- [pydantic.networks.IPvAnyNetwork][] and [ipaddress.IPv4Network][]/[ipaddress.IPv6Network][]
- [pydantic.networks.IPvAnyInterface][] and [ipaddress.IPv4Interface][]/[ipaddress.IPv6Interface][]

But you can register some custom types using [`register_pydanclick_string_type`][pydanclick.register_pydanclick_string_type].

The following example use both Pydantic builtin types and register some custom types
([`Color`][pydantic_extra_types.color.Color] and [`MacAddress`][pydantic_extra_types.mac_address.MacAddress]):

```python
--8<--
known_types.py
--8<--
```

You can see that each type has its own specific `METAVAR`:

```console
$ python examples/known_types.py --help
Usage: known_types.py [OPTIONS]

  An example showing known Pydantic types support.

Options:
  --secret SECRET
  --url URL
  --postgres-dsn URL
  --email EMAIL
  --name-email EMAIL
  --ip IP
  --net NETWORK
  --iface IFACE
  --color COLOR
  --mac MAC
  --help              Show this message and exit.
```

You can try submitting a parameter and you will see they are properly parsed from string:

```console
$ python examples/known_types.py --url https://felix-martel.github.io/pydanclick/
{
  "url": "https://felix-martel.github.io/pydanclick/"
}
$ python examples/known_types.py --secret my-secret
{
  "secret": "**********"
}
```
