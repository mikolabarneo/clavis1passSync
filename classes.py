class secret:
    def __init__(self) -> None:
        self.clavisId = 0
        self.category = 'LOGIN'
        self.version = 1
        self.tags = []
        self.fields = []
        section = clavisSection()
        section.label = self.clavisId
        self.sections = [section]
        self.title = ''
        self.urls = []
        self.vault = vault()
        self.folder = folder()
        self.fields = []
    def buildTags(self):
        self.tags = self.folder.folderPath.strip('\\').split('\\')

    def toJson(self):
        return {
            "additionalInformation": "test",
            "category": self.category,
            "version": self.version,
            "tags": self.tags,
            "fields": [field.__dict__ for field in self.fields],
            "sections": [section.__dict__ for section in self.sections],
            "title": self.title,
            "urls": self.urls,
            "vault": self.vault.__dict__
        }

class vault:
    def __init__(self) -> None:
        self.id = 0
        self.name = ''

class folder:
    def __init__(self) -> None:
        self.id = 0
        self.folderPath = ''
        self.folderName = ''
        self.parentFolderId = 0
        self.rootFolderId = 0

class clavisSection:
    def __init__(self) -> None:
        self.id = 'qi5thupeodxuju6hxnbq3ixw2y'
        self.label = 0

class secretField:
    def __init__(self) -> None:
        self.id = 'password'
        self.type = 'CONCEALED'
        self.label = 'password'
        self.value = 'some_password'
        self.purpose = 'PASSWORD'