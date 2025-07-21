import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re

def geodetic_to_enu(lat, lon, alt, lat0=None, lon0=None, alt0=None):
    """
    Approximate local East-North-Up (metres) for small regions.
    lat, lon in degrees, alt in metres.
    """
    lat  = np.radians(lat)
    lon  = np.radians(lon)
    lat0 = np.radians(np.mean(lat)  if lat0 is None else lat0)
    lon0 = np.radians(np.mean(lon)  if lon0 is None else lon0)
    alt0 = np.mean(alt) if alt0 is None else alt0

    # WGS-84 radii of curvature (≈)
    R_E = 6378137.0          # equatorial radius (m)
    R_N = 6356752.3          # polar radius      (m)

    # metres per radian at reference latitude
    m_per_lat = R_N
    m_per_lon = R_E * np.cos(lat0)

    d_lat = lat - lat0
    d_lon = lon - lon0
    d_alt = alt - alt0

    north = d_lat * m_per_lat          # y
    east  = d_lon * m_per_lon          # x
    up    = d_alt                      # z (positive up)

    return east, north, up

def set_axes_equal(ax, min_radius=1.0):
    """
    Make 3-D axes equal and add a fallback *min_radius* (metres)
    so nearly-flat data still occupy a visible cube.
    """
    xlim = ax.get_xlim3d()
    ylim = ax.get_ylim3d()
    zlim = ax.get_zlim3d()

    # half-ranges
    half_ranges = [abs(xlim[1]-xlim[0])*0.5,
                   abs(ylim[1]-ylim[0])*0.5,
                   abs(zlim[1]-zlim[0])*0.5]

    # largest half-range, but never smaller than min_radius
    plot_radius = max(max(half_ranges), min_radius)

    x_mid = np.mean(xlim)
    y_mid = np.mean(ylim)
    z_mid = np.mean(zlim)

    ax.set_xlim3d(x_mid - plot_radius, x_mid + plot_radius)
    ax.set_ylim3d(y_mid - plot_radius, y_mid + plot_radius)
    ax.set_zlim3d(z_mid - plot_radius, z_mid + plot_radius)

def _create_empty_data_dict():
    """Yardımcı fonksiyon: Veri saklamak için boş bir sözlük oluşturur."""
    return {
        "interceptor_location": [],
        "target_location": [],
        "velocity": [],
        "velocity_norm": [],
        "desired_accel": [],
        "virtual_accel_inertial": [],
        "attitude": [],
        "control_commands": [],
        "cbf_value": [],
        "xyz_pseudo": [],
        "throttle": [],
        "timestamps": [],
        "pixel_errors": [],
        "depth": [],  # <-- YENİ: Depth verisi için liste eklendi
        "total_desired_acc": [],  # <-- YENİ: Toplam istenen ivme için liste eklendi
        "target_yaw": [],  # <-- YENİ: Hedef yaw açısı için liste eklendi
        "target_velocity": [],  # <-- YENİ: Hedef hız için liste eklendi
        "target_yaw_new": [],
    }

def parse_log_file_segmented(log_file_content):
    """
    Log dosyasını okuyarak "GUIDED" modundaki her bir oturumu ayrı bir test olarak ayrıştırır.
    """
    sessions = []
    current_session_data = None

    for line in log_file_content.splitlines():
        if "Drone mode: GUIDED" in line:
            if current_session_data is None:
                current_session_data = _create_empty_data_dict()
                sessions.append(current_session_data)

        elif "Drone mode:" in line and "GUIDED" not in line:
            current_session_data = None

        if current_session_data:
            try:
                current_timestamp = line.split(' - ')[0]
            except IndexError:
                continue

            if "Interceptor Location" in line:
                try:
                    loc_str = re.search(r'\((.*?)\)', line).group(1)
                    current_session_data["interceptor_location"].append(list(map(float, loc_str.split(', '))))
                    current_session_data["timestamps"].append(current_timestamp)
                except (AttributeError, ValueError):
                    continue
            elif "Pixel errors:" in line:
                try:
                    loc_str = re.search(r'\((.*?)\)', line).group(1)
                    target_loc = list(map(float, loc_str.split(', ')))
                    current_session_data["pixel_errors"].append(target_loc)
                except (AttributeError, ValueError):
                    continue
            
            # YENİ: Depth verisini ayrıştıran blok
            elif "Depth:" in line:
                try:
                    # "Depth: " ifadesinden sonraki sayısal değeri bulur
                    depth_val = float(re.search(r"Depth:\s*([-\d\.]+)", line).group(1))
                    current_session_data["depth"].append(depth_val)
                except (AttributeError, ValueError):
                    continue

            elif "Target Location" in line:
                try:
                    loc_str = re.search(r'\((.*?)\)', line).group(1)
                    target_loc = list(map(float, loc_str.split(', ')))
                    current_session_data["target_location"].append(target_loc)
                except (AttributeError, ValueError):
                    continue
            elif "Velocity:" in line:
                try:
                    vel_str = re.search(r'\[(.*?)\]', line).group(1)
                    velocity = list(map(float, vel_str.split(', ')))
                    current_session_data["velocity"].append(velocity)
                    current_session_data["velocity_norm"].append(np.linalg.norm(velocity))
                except (AttributeError, ValueError):
                    continue
            elif "Desired Acceleration" in line:
                try:
                    acc_str = re.search(r'\[(.*?)\]', line).group(1)
                    current_session_data["desired_accel"].append([float(x) for x in acc_str.split()])
                except (AttributeError, ValueError):
                    continue
            
            elif "Virtual Acceleration Inertial XY:" in line and "Virtual Acceleration Inertial Z:" in line:
                try:
                    match_xy = re.search(r"Virtual Acceleration Inertial XY:\s*\[\s*([-\d\.e]+)\s+([-\d\.e]+)\s+([-\d\.e]+)\s*\]", line)
                    match_z = re.search(r"Virtual Acceleration Inertial Z:\s*\[\s*([-\d\.e]+)\s+([-\d\.e]+)\s+([-\d\.e]+)\s*\]", line)

                    if match_xy and match_z:
                        accel_x = float(match_xy.group(1))
                        accel_y = float(match_xy.group(2))
                        accel_z = float(match_z.group(3))
                        final_accel = [accel_x, accel_y, accel_z]
                        current_session_data["virtual_accel_inertial"].append(final_accel)
                except (AttributeError, ValueError, IndexError):
                    continue

            elif "Accel Desired: " in line:
                try:
                    match_tot_acc = re.search(r"Accel Desired:\s*\[\s*([-\d\.e]+)\s+([-\d\.e]+)\s+([-\d\.e]+)\s*\]", line)

                    if match_tot_acc:
                        accel_x = float(match_tot_acc.group(1))
                        accel_y = float(match_tot_acc.group(2))
                        accel_z = float(match_tot_acc.group(3))
                        final_accel = [accel_x, accel_y, accel_z]
                        current_session_data["total_desired_acc"].append(final_accel)
                except (AttributeError, ValueError, IndexError):
                    continue
            
            elif "Attitude:" in line:
                try:
                    att_str = re.search(r'\((.*?)\)', line).group(1)
                    current_session_data["attitude"].append(list(map(float, att_str.split(', '))))
                except (AttributeError, ValueError):
                    continue
            elif "Control Commands - Pitch" in line:
                try:
                    pitch = float(re.search(r'Pitch: ([\-0-9.]+)', line).group(1))
                    yaw = float(re.search(r'Yaw: ([\-0-9.]+)', line).group(1))
                    roll = float(re.search(r'Roll: ([\-0-9.]+)', line).group(1))
                    throttle = float(re.search(r'Thrust: ([\-0-9.]+)', line).group(1))
                    current_session_data["control_commands"].append([pitch, yaw, roll])
                    current_session_data["throttle"].append(throttle)
                except (AttributeError, ValueError):
                    continue
            elif "CBF:" in line:
                try:
                    cbf_str = re.search(r'\[(.*?)\]', line).group(1)
                    current_session_data["cbf_value"].append(float(cbf_str))
                except (AttributeError, ValueError):
                    continue
            elif "XYZPseudoFrame:" in line:
                try:
                    xyz_str = re.search(r'\[(.*?)\]', line).group(1)
                    current_session_data["xyz_pseudo"].append([float(x) for x in xyz_str.split()])
                except (AttributeError, ValueError):
                    continue

            elif "Target Yaw:" in line:
                try:
                    tgt_yaw_str = re.search(r"([-+]?\d*\.\d+)", line).group(1)
                    target_yaw = float(tgt_yaw_str)
                    current_session_data["target_yaw"].append(target_yaw)
                except (AttributeError, ValueError):
                    continue

            elif "Target Heading New:" in line:
                try:
                    tgt_yaw_str = re.search(r"([-+]?\d*\.\d+)", line).group(1)
                    target_yaw = float(tgt_yaw_str)
                    current_session_data["target_yaw_new"].append(target_yaw)
                except (AttributeError, ValueError):
                    continue
            elif "Target Velocity:" in line:
                try:
                    # Örnek satır: "Target Velocity: Vx: -0.03, Vy: -13.66, Vz: -0.18"
                    match = re.search(
                        r"Vx:\s*([-\d\.]+),\s*Vy:\s*([-\d\.]+),\s*Vz:\s*([-\d\.]+)",
                        line
                    )
                    if match:
                        vx = float(match.group(1))
                        vy = float(match.group(2))
                        vz = float(match.group(3))
                        current_session_data["target_velocity"].append([vx, vy, vz])
                except (AttributeError, ValueError):
                    continue

    return sessions

def plot_segmented_data(sessions):
    """
    Ayrıştırılmış oturum verilerini kullanarak grafikleri çizer.
    """
    if not sessions:
        print("Çizilecek veri bulunamadı.")
        return

    # 1. 3D Trajectory Plot
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    for i, session in enumerate(sessions):
        if session["interceptor_location"]:
            # unpack lat, lon, alt
            lat, lon, alt = np.array(session["interceptor_location"]).T
            x, y, z = geodetic_to_enu(lat, lon, alt)
            p = ax.plot(x, y, z,
                        label=f'Test {i+1} Interceptor')
        if session["target_location"]:
            lat, lon, alt = np.array(session["target_location"]).T
            x, y, z = geodetic_to_enu(lat, lon, alt)
            ax.plot(x, y, z,
                    label=f'Test {i+1} Target',
                    linestyle='--', color=p[0].get_color())

    ax.set_xlabel('East (m)')
    ax.set_ylabel('North (m)')
    ax.set_zlabel('Up (m)')
    ax.set_title('3-D Interceptor and Target Trajectories')

    set_axes_equal(ax, min_radius=10.0)   # tweak min_radius to taste
    ax.legend()
    plt.show()
    

    # 2. Tek Boyutlu Veriler İçin Çizim Fonksiyonu
    def plot_single_dim(title, ylabel, data_key, label):
        # Veri içeren oturumları filtrele
        valid_sessions = [s for s in sessions if s.get(data_key)]
        if not valid_sessions:
            print(f"'{title}' için çizilecek veri bulunamadı.")
            return

        plt.figure(figsize=(12, 6))
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel('Time Steps (in GUIDED mode)')
        for i, session in enumerate(valid_sessions):
            session_id = sessions.index(session) + 1
            data_array = np.array(session[data_key])
            timestamps = np.arange(len(data_array))
            plt.plot(timestamps, data_array, label=f'Test {session_id} - {label}')
        plt.legend()
        plt.grid(True)
        plt.show()

    # 3. Çok Boyutlu Veriler İçin Çizim Fonksiyonuq
    def plot_multidim_subplots(fig_title, ylabel, data_key, component_labels):
        valid_sessions = [s for s in sessions if s.get(data_key)]
        if not valid_sessions:
            print(f"'{fig_title}' için çizilecek veri bulunamadı.")
            return
        
        num_sessions = len(valid_sessions)
        fig, axes = plt.subplots(num_sessions, 1, figsize=(12, 4 * num_sessions), sharex=True, squeeze=False)
        fig.suptitle(fig_title, fontsize=16)
        
        axes = axes.flatten()

        for i, (session, ax) in enumerate(zip(valid_sessions, axes)):
            session_id = sessions.index(session) + 1
            ax.set_title(f'Test {session_id}')
            ax.grid(True)
            ax.set_ylabel(ylabel)
            data_array = np.array(session[data_key])
            timestamps = np.arange(len(data_array))
            for j, label in enumerate(component_labels):
                ax.plot(timestamps, data_array[:, j], label=label)
            ax.legend()
        
        axes[-1].set_xlabel('Time Steps (in GUIDED mode)')
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        plt.show()

    # Grafikleri çizdirme
    plot_multidim_subplots('Velocity Components', 'Velocity (m/s)', 'velocity', ['V_x', 'V_y', 'V_z'])
    plot_multidim_subplots('Desired Acceleration - Pixel', 'Acceleration (m/s^2)', 'desired_accel', ['Acc_x', 'Acc_y', 'Acc_z'])
    plot_multidim_subplots('Virtual Acceleration Inertial', 'Acceleration (m/s^2)', 'virtual_accel_inertial', ['VAcc_x', 'VAcc_y', 'VAcc_z'])
    plot_multidim_subplots('Control Commands', 'Control Command', 'control_commands', ['Pitch', 'Yaw', 'Roll'])
    plot_multidim_subplots('XYZPseudoFrame', 'Position (m)', 'xyz_pseudo', ['X', 'Y', 'Z'])
    plot_multidim_subplots('Pixel Errors', 'Error (pixels)', 'pixel_errors', ['X_err', 'Y_err'])
    plot_multidim_subplots('Total Desired Acceleration', 'Acceleration (m/s^2)', 'total_desired_acc', ['Total Acc_x', 'Total Acc_y', 'Total Acc_z'])
    plot_multidim_subplots('Target Velocity', 'Velocity (m/s)', 'target_velocity', ['Vx', 'Vy', 'Vz'])

    # Attitude Plot
    valid_sessions_att = [s for s in sessions if s.get("attitude")]
    if valid_sessions_att:
        num_sessions = len(valid_sessions_att)
        fig, axes = plt.subplots(num_sessions, 1, figsize=(12, 4 * num_sessions), sharex=True, squeeze=False)
        fig.suptitle('Attitude (Roll, Pitch, Yaw)', fontsize=16)
        axes = axes.flatten()
        for i, (session, ax) in enumerate(zip(valid_sessions_att, axes)):
            session_id = sessions.index(session) + 1
            ax.set_title(f'Test {session_id}')
            ax.grid(True)
            ax.set_ylabel('Angle (degrees)')
            attitudes = np.array(session["attitude"])
            timestamps = np.arange(len(attitudes))
            ax.plot(timestamps, np.rad2deg(attitudes[:, 0]), label='Roll')
            ax.plot(timestamps, np.rad2deg(attitudes[:, 1]), label='Pitch')
            ax.plot(timestamps, np.rad2deg(attitudes[:, 2]), label='Yaw')
            ax.legend()
        axes[-1].set_xlabel('Time Steps (in GUIDED mode)')
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        plt.show()
    
    # 4. Combined Yaw Comparison Plot
    valid_yaw_sessions = [
        s for s in sessions 
        if s.get("target_yaw") and s.get("target_yaw_new")
    ]
    if valid_yaw_sessions:
        plt.figure(figsize=(12, 6))
        plt.title('Target Yaw vs. Target Heading New')
        plt.ylabel('Yaw (degrees)')
        plt.xlabel('Time Steps (in GUIDED mode)')
        for session in valid_yaw_sessions:
            idx = sessions.index(session) + 1
            ty = np.array(session["target_yaw"])
            thn = np.array(session["target_yaw_new"])
            t = np.arange(len(ty))
            plt.plot(t, ty, label=f'Test {idx} Target Yaw')
            plt.plot(t, thn, linestyle='--', label=f'Test {idx} Heading New')
        plt.legend()
        plt.grid(True)
        plt.show()
    else:
        print("Combined yaw data bulunamadı.")

    # Tek boyutlu grafikler
    plot_single_dim('Normed Velocity over Time', 'Velocity Norm (m/s)', 'velocity_norm', 'Norm')
    plot_single_dim('CBF Value over Time', 'CBF Value', 'cbf_value', 'CBF')
    plot_single_dim('Throttle over Time', 'Throttle', 'throttle', 'Throttle')
    plot_single_dim('Depth over Time', 'Depth (m)', 'depth', 'Depth') # <-- YENİ: Depth grafiği çağrısı eklendi
    plot_single_dim('Target Yaw over Time', 'Yaw (degrees)', 'target_yaw', 'Target Yaw')  # <-- YENİ: Target Yaw grafiği çağrısı eklendi
    plot_single_dim('Target Yaw New over Time', 'Yaw (degrees)', 'target_yaw_new', 'Target Yaw New')  #


if __name__ == "__main__":
    try:
        # Lütfen log dosyanızın adını ve yolunu güncelleyin
        with open('log.log', 'r') as file:
            log_file_content = file.read()
        
        parsed_sessions = parse_log_file_segmented(log_file_content)
        
        if not parsed_sessions:
            print("Log dosyasında 'GUIDED' modunda hiçbir oturum bulunamadı.")
        else:
            print(f"Toplam {len(parsed_sessions)} adet 'GUIDED' mod test oturumu bulundu. Grafikler oluşturuluyor...")
            plot_segmented_data(parsed_sessions)

    except FileNotFoundError:
        print("Hata: Log dosyası bulunamadı. Lütfen dosya yolunu kontrol edin.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")