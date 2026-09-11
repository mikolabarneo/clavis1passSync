class secret:
    def __init__(self) -> None:
        self.clavisId = 0
        self.category = 'LOGIN'
        self.version = 0
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

class vault:
    def __init__(self) -> None:
        self.id = 0
        self.name = ''
        self.type = 'PERSONAL'

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