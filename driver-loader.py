import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll

# https://gist.github.com/santa4nt/11068180

LPDWORD = ctypes.POINTER(wintypes.DWORD)
LPOVERLAPPED = wintypes.LPVOID
LPSECURITY_ATTRIBUTES = wintypes.LPVOID

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_EXECUTE = 0x20000000
GENERIC_ALL = 0x10000000

CREATE_NEW = 1
CREATE_ALWAYS = 2
OPEN_EXISTING = 3
OPEN_ALWAYS = 4
TRUNCATE_EXISTING = 5

FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = -1

NULL = 0
FALSE = wintypes.BOOL(0)
TRUE = wintypes.BOOL(1)

#Service access constants - see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms685981(v=vs.85).aspx

SERVICE_ALL_ACCESS = 0xF01FF
SERVICE_CHANGE_CONFIG = 0x0002
SERVICE_ENUMERATE_DEPENDENTS = 0x0008
SERVICE_INTERROGATE = 0x0080
SERVICE_PAUSE_CONTINUE = 0x0040
SERVICE_QUERY_CONFIG = 0x0001
SERVICE_QUERY_STATUS = 0x0004
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020
SERVICE_USER_DEFINED_CONTROL = 0x0100

#service control constants - see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms682108(v=vs.85).aspx
SERVICE_CONTROL_CONTINUE = 0x00000003
SERVICE_CONTROL_INTERROGATE = 0x00000004
SERVICE_CONTROL_NETBINDADD = 0x00000007
SERVICE_CONTROL_NETBINDDISABLE = 0x0000000A
SERVICE_CONTROL_NETBINDENABLE = 0x00000009
SERVICE_CONTROL_NETBINDREMOVE = 0x00000008
SERVICE_CONTROL_PARAMCHANGE = 0x00000006
SERVICE_CONTROL_PAUSE = 0x00000002
SERVICE_CONTROL_STOP = 0x00000001

#service type constants - see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms682450(v=vs.85).aspx
SERVICE_ADAPTER = 0x00000004
SERVICE_FILE_SYSTEM_DRIVER = 0x00000002
SERVICE_KERNEL_DRIVER = 0x00000001
SERVICE_RECOGNIZER_DRIVER = 0x00000008
SERVICE_WIN32_OWN_PROCESS = 0x00000010
SERVICE_WIN32_SHARE_PROCESS = 0x00000020

#service start options constants - see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms682450(v=vs.85).aspx
SERVICE_AUTO_START = 0x00000002
SERVICE_BOOT_START = 0x00000000
SERVICE_DEMAND_START = 0x00000003
SERVICE_DISABLED = 0x00000004
SERVICE_SYSTEM_START = 0x00000001

#service error control constants - see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms682450(v=vs.85).aspx
SERVICE_ERROR_CRITICAL = 0x00000003
SERVICE_ERROR_IGNORE = 0x00000000
SERVICE_ERROR_NORMAL = 0x00000001
SERVICE_ERROR_SEVERE = 0x00000002

def install_driver(name, pe_path):
	service_handle = create_service(
		driver_name,
		driver_name,
		SERVICE_ALL_ACCESS,
		SERVICE_KERNEL_DRIVER,
		SERVICE_DEMAND_START,
		SERVICE_ERROR_IGNORE,
		pe_path,
		None,
		None,
		None,
		None,
		None
	)
	if service_handle == NULL:
		return False
	close_service_handle(service_handle)
	return True

def uninstall_driver(service_manager_handle, driver_name, driver_pe_path):
	service_handle = open_service(service_manager_handle, driver_name, SERVICE_ALL_ACCESS)
	if not service_handle:
		return False
	ret = delete_service(service_handle)
	close_service_handle(service_handle)
	return ret

def start_driver(service_manager_handle, driver_name):
	service_handle = open_service(service_manager_handle, driver_name, SERVICE_ALL_ACCESS)
	if not service_handle:
		return False
	ret = start_service(service_handle,0,NULL)
	close_service_handle(service_handle)
	return ret
	
def stop_driver(service_manager_handle, driver_name):
	service_handle = open_service(service_manager_handle, driver_name, SERVICE_ALL_ACCESS)
	if not service_handle:
		return False
	service_status = wintypes.SERVICE_STATUS
	ret = control_service(service_handle, SERVICE_CONTROL_STOP, ctypes.byref(service_status))
	close_service_handle(service_handle)
	return ret

def open_device(device_path, access, mode, creation, flags):
	"""See: CreateFile function
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    """
    CreateFile_Fn = windll.kernel32.CreateFileW
    CreateFile_Fn.argtypes = [
            wintypes.LPWSTR,                    # _In_          LPCTSTR lpFileName
            wintypes.DWORD,                     # _In_          DWORD dwDesiredAccess
            wintypes.DWORD,                     # _In_          DWORD dwShareMode
            LPSECURITY_ATTRIBUTES,              # _In_opt_      LPSECURITY_ATTRIBUTES lpSecurityAttributes
            wintypes.DWORD,                     # _In_          DWORD dwCreationDisposition
            wintypes.DWORD,                     # _In_          DWORD dwFlagsAndAttributes
            wintypes.HANDLE]                    # _In_opt_      HANDLE hTemplateFile
    CreateFile_Fn.restype = wintypes.HANDLE

    return wintypes.HANDLE(CreateFile_Fn(device_path,
                         access,
                         mode,
                         NULL,
                         creation,
                         flags,
                         NULL))

def send_ioctl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz,):
	"""See: DeviceIoControl function
    http://msdn.microsoft.com/en-us/library/aa363216(v=vs.85).aspx
    """
    DeviceIoControl_Fn = windll.kernel32.DeviceIoControl
    DeviceIoControl_Fn.argtypes = [
            wintypes.HANDLE,                    # _In_          HANDLE hDevice
            wintypes.DWORD,                     # _In_          DWORD dwIoControlCode
            wintypes.LPVOID,                    # _In_opt_      LPVOID lpInBuffer
            wintypes.DWORD,                     # _In_          DWORD nInBufferSize
            wintypes.LPVOID,                    # _Out_opt_     LPVOID lpOutBuffer
            wintypes.DWORD,                     # _In_          DWORD nOutBufferSize
            LPDWORD,                            # _Out_opt_     LPDWORD lpBytesReturned
            LPOVERLAPPED]                       # _Inout_opt_   LPOVERLAPPED lpOverlapped
    DeviceIoControl_Fn.restype = wintypes.BOOL

    # allocate a DWORD, and take its reference
    dwBytesReturned = wintypes.DWORD(0)
    lpBytesReturned = ctypes.byref(dwBytesReturned)

    status = DeviceIoControl_Fn(devhandle,
                  ioctl,
                  inbuf,
                  inbufsiz,
                  outbuf,
                  outbufsiz,
                  lpBytesReturned,
                  None)

    return status, dwBytesReturned
def load_device_driver():
 const TCHAR * Name, const TCHAR * Path, 
					  HANDLE * lphDevice, PDWORD Error )
{
	SC_HANDLE	schSCManager;
	BOOL		okay;

	schSCManager = OpenSCManager( NULL, NULL, SC_MANAGER_ALL_ACCESS );

	// Remove old instances
	RemoveDriver( schSCManager, Name );

	// Ignore success of installation: it may already be installed.
	InstallDriver( schSCManager, Name, Path );

	// Ignore success of start: it may already be started.
	StartDriver( schSCManager, Name );

	// Do make sure we can open it.
	okay = OpenDevice( Name, lphDevice );
	*Error = GetLastError();
 	CloseServiceHandle( schSCManager );

	return okay;
def unload_device_driver():
SC_HANDLE	schSCManager;

	schSCManager = OpenSCManager(	NULL,                 // machine (NULL == local)
                              		NULL,                 // database (NULL == default)
									SC_MANAGER_ALL_ACCESS // access required
								);

	StopDriver( schSCManager, Name );
	RemoveDriver( schSCManager, Name );
	 
	CloseServiceHandle( schSCManager );

	return TRUE;
def ctl_code(device_type, function, method, access):
	return (device_type << 16) | (access << 14) | function << 2 | method

################################
# Lower level support functions
################################

def create_service(service_manager_handle, service_name, display_name, desired_access, service_type, start_type, 
					error_control, binary_path, load_order_group, tag_id, dependencies, service_start_name, password):
	"""See: CreateService function
	https://msdn.microsoft.com/en-gb/library/windows/desktop/ms682450(v=vs.85).aspx
	"""

	CreateService_Fn = windll.Advapi32.CreateService	#SC_HANDLE WINAPI CreateService(
	CreateService_Fn.argtypes = [						#
		wintypes.SC_HANDLE,								#	_In_      SC_HANDLE hSCManager,
		wintypes.LPCTSTR,								#	_In_      LPCTSTR   lpServiceName,	
		wintypes.LPCTSTR,								#	_In_opt_  LPCTSTR   lpDisplayName,
		wintypes.DWORD,									#	_In_      DWORD     dwDesiredAccess,
		wintypes.DWORD,									#	_In_      DWORD     dwServiceType,
		wintypes.DWORD,									#	_In_      DWORD     dwStartType,	
		wintypes.DWORD,									#	_In_      DWORD     dwErrorControl,
		wintypes.LPCTSTR,								#	_In_opt_  LPCTSTR   lpBinaryPathName,
		wintypes.LPCTSTR,								#	_In_opt_  LPCTSTR   lpLoadOrderGroup,
		wintypes.LPDWORD,								#	_Out_opt_ LPDWORD   lpdwTagId,
		wintypes.LPCTSTR,								#	_In_opt_  LPCTSTR   lpDependencies,	
		wintypes.LPCTSTR,								#	_In_opt_  LPCTSTR   lpServiceStartName,
		wintypes.LPCTSTR								#	_In_opt_  LPCTSTR   lpPassword
	]
	ControlService_Fn.restype = wintypes.SC_HANDLE
	handle = ControlService_Fn(
		service_manager_handle, 
		service_name, 
		display_name, 
		desired_access, 
		service_type, 
		start_type, 
		error_control,
		binary_path,
		load_order_group,
		tag_id,
		dependencies,
		service_start_name,
		password
	)
	return handle

def open_service(service_manager_handle, service_name, desired_access):
	""" See: OpenService function
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms684330(v=vs.85).aspx
	"""
	OpenService_Fn = windll.Advapi32.OpenService 	#SC_HANDLE WINAPI OpenService(
	OpenService_Fn.argtypes = [						#
		wintypes.HANDLE,							#	_In_ SC_HANDLE hSCManager,
		wintypes.LPCTSTR,							#	_In_ LPCTSTR   lpServiceName,
		wintypes.DWORD								#	_In_ DWORD     dwDesiredAccess
	]
	OpenService_Fn.restype = wintypes.SC_HANDLE
	handle = OpenService_Fn(
		service_manager_handle,
		service_name,
		desired_access
	)
	return handle

def control_service(service_handle, control, service_status):
	"""See: ControlService function
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms682108(v=vs.85).aspx
	"""
	ControlService_Fn = windll.Advapi32.ControlService	 	#BOOL WINAPI ControlService(
	ControlService_Fn.argtypes = [							#
		wintypes.SC_HANDLE									#	_In_  SC_HANDLE        hService,
		wintypes.DWORD										#	_In_  DWORD            dwControl,
		wintypes.LPSERVICE_STATUS							#	_Out_ LPSERVICE_STATUS lpServiceStatus
	]
	ControlService_Fn.restype = wintypes.BOOL
	bool = ControlService_Fn(
		service_handle,
		control,
		service_status
	)
	return bool
	
def close_service_handle(service_handle):
	"""See: CloseServiceHandle function 
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms682028(v=vs.85).aspx
	"""
	CloseServiceHandle_Fn = windll.Advapi32.CloseServiceHandle	#BOOL WINAPI CloseServiceHandle(
	CloseServiceHandle_Fn.argtypes = [
		wintypes.SC_HANDLE										#	_In_ SC_HANDLE hSCObject
	]
	CloseServiceHandle_Fn.restype = wintypes.BOOL
	bool = CloseServiceHandle_Fn(
		service_handle
	)
	return bool

def delete_service(service_handle):
	"""See: DeleteService function
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms682562(v=vs.85).aspx
	"""
	DeleteService_Fn = windll.Advapi32.DeleteService	#BOOL WINAPI DeleteService(
	DeleteService_Fn.argtypes = [						#
		wintypes.SC_HANDLE								#	_In_ SC_HANDLE hService
	]
	DeleteService_Fn.restype = wintypes.BOOL
	bool = DeleteService_Fn(
		service_handle
	)
	return bool
	
def open_sc_manager(machine_name, database_name, desired_access):
	"""See: OpenSCManager function
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms684323(v=vs.85).aspx
	"""
	OpenSCManager_Fn = windll.Advapi32.OpenSCManager	#SC_HANDLE WINAPI OpenSCManager(
	OpenSCManager_Fn.argtypes = [						#
		wintypes.LPCTSTR,								#	_In_opt_ LPCTSTR lpMachineName,
		wintypes.LPCTSTR,								#	_In_opt_ LPCTSTR lpDatabaseName,
		wintypes.DWORD									#	_In_     DWORD   dwDesiredAccess
	]
	OpenSCManager_Fn.restype = wintypes.SC_HANDLE
	handle = OpenSCManager_Fn(
		machine_name,
		database_name,
		desired_access
	)
	return handle
	
def start_service(service_handle, service_arg_count, service_arg_vectors):
	"""See: StartService function
	https://msdn.microsoft.com/en-us/library/windows/desktop/ms686321(v=vs.85).aspx
	"""
	
	StartService_Fn = windll.Advapi32.StartService	#BOOL WINAPI StartService(
	StartService_Fn.argtypes = [					#
		wintypes.SC_HANDLE,							#	_In_ 	 SC_HANDLE hService,
		wintypes.DWORD,								#	_In_ 	 DWORD     dwNumServiceArgs,
		wintypes.LPCTSTR							#	_In_opt_ LPCTSTR   *lpServiceArgVectors
	]
	StartService_Fn.restype = wintypes.BOOL
	bool = StartService_Fn(
		service_handle,
		service_arg_count, 
		service_arg_vectors
	)
	return bool
if __name__ == "__main__":
