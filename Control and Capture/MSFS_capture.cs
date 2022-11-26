using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using System.Windows.Forms;

// Add these two statements to all SimConnect clients
using Microsoft.FlightSimulator.SimConnect;
using System.Runtime.InteropServices;
using System.Drawing.Imaging;


namespace ViewControl
{
    public partial class Form1 : Form
    {
        #region 初始化
        SimConnect simconnect = null;

        // Object IDs
        uint A320ID = 0;

        private enum DATA_REQUESTS
        {
            REQUEST_1,
        }

        private enum AIObject_REQUESTS
        {
            REQUEST_ADD_A320,
            REQUEST_REMOVE_A320
        }

        private enum DEFINITIONS
        {
            Struct1,
            Struct2,
        }

        private enum DEFINITIONS_WAYPOINT
        {
            WAYPOINT_TAKEOFF
        }

        private enum EVENTS
        {
            KEY_CLOCK_HOURS_INC,
            KEY_CLOCK_HOURS_DEC,
            KEY_CLOCK_HOURS_SET,
            KEY_CLOCK_MINUTE_SET
        }
        private enum NOTIFICATION_GROUPS
        {
            GROUP0,
        }
        private struct Struct1
        {
            public double longitude;
            public double latitude;
            public double altitude;
            public double pitch;
            public double bank;
            public double heading;
            public double airspeed;
        }
        #endregion

        ScreenCapturor sc = new ScreenCapturor();
        public Form1()
        {
            InitializeComponent();
            setButtons(true, false);
            comboBoxAction.SelectedIndex = 0;
        }
        private void initDataRequest()
        {
            try
            {
                simconnect.OnRecvOpen += new SimConnect.RecvOpenEventHandler(simconnect_OnRecvOpen);
                simconnect.OnRecvQuit += new SimConnect.RecvQuitEventHandler(simconnect_OnRecvQuit);
                simconnect.OnRecvException += new SimConnect.RecvExceptionEventHandler(simconnect_OnRecvException);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "Plane Longitude", "degrees", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "Plane Latitude", "degrees", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "PLANE ALTITUDE", "feet", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "PLANE PITCH DEGREES", "degrees", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "PLANE BANK DEGREES", "degrees", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "PLANE HEADING DEGREES TRUE", "degrees", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct1, "AIRSPEED INDICATED", "knots", SIMCONNECT_DATATYPE.FLOAT64, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS.Struct2, "INITIAL POSITION", null, SIMCONNECT_DATATYPE.INITPOSITION, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.AddToDataDefinition(DEFINITIONS_WAYPOINT.WAYPOINT_TAKEOFF, "AI WAYPOINT LIST", "number", SIMCONNECT_DATATYPE.WAYPOINT, 0.0f, SimConnect.SIMCONNECT_UNUSED);
                simconnect.RegisterDataDefineStruct<Struct1>(DEFINITIONS.Struct1);
                simconnect.OnRecvSimobjectDataBytype += new SimConnect.RecvSimobjectDataBytypeEventHandler(simconnect_OnRecvSimobjectDataBytype);
                simconnect.OnRecvAssignedObjectId += new SimConnect.RecvAssignedObjectIdEventHandler(simconnect_OnRecvAssignedObjectID);
            }
            catch (COMException exception1)
            {
                //displayText(exception1.Message);
            }
        }

        #region MSFS2020 默认函数
        private void simconnect_OnRecvSimobjectDataBytype(SimConnect sender, SIMCONNECT_RECV_SIMOBJECT_DATA_BYTYPE data)
        {
            switch ((DATA_REQUESTS)data.dwRequestID)
            {
                case DATA_REQUESTS.REQUEST_1:
                    Struct1 struct1 = (Struct1)data.dwData[0];

                    textBoxLongitude.Text = struct1.longitude.ToString();
                    textBoxLatitude.Text = struct1.latitude.ToString();
                    textBoxAltitude.Text = struct1.altitude.ToString();
                    textBoxPitch.Text = struct1.pitch.ToString();
                    textBoxBank.Text = struct1.bank.ToString();
                    textBoxHeading.Text = struct1.heading.ToString();
                    textBoxAirspeed.Text = struct1.airspeed.ToString();
                    break;
            }
        }

        private void simconnect_OnRecvEvent(SimConnect sender, SIMCONNECT_RECV_EVENT data)
        {

        }

        private void simconnect_OnRecvAssignedObjectID(SimConnect sender, SIMCONNECT_RECV_ASSIGNED_OBJECT_ID data)
        {
            switch ((AIObject_REQUESTS)data.dwRequestID)
            {
                case AIObject_REQUESTS.REQUEST_ADD_A320:
                    A320ID = (uint)(AIObject_REQUESTS)data.dwObjectID;
                    //timerDynamicPlaneSet.Start();
                    label10.Text = "A320 Set:" + A320ID.ToString();
                    break;
                case AIObject_REQUESTS.REQUEST_REMOVE_A320:
                    A320ID = 0;
                    break;
            }
        }
        protected override void DefWndProc(ref Message m)
        {
            if (m.Msg == 0x402)
            {
                if (simconnect != null)
                {
                    simconnect.ReceiveMessage();
                }
            }
            else
            {
                base.DefWndProc(ref m);
            }
        }
        private void simconnect_OnRecvException(SimConnect sender, SIMCONNECT_RECV_EXCEPTION data)
        {
            labelConnectStatus.Text = "Exception received: " + ((uint)data.dwException);
        }

        private void simconnect_OnRecvOpen(SimConnect sender, SIMCONNECT_RECV_OPEN data)
        {
            labelConnectStatus.Text = "Connected to sim";
        }

        private void simconnect_OnRecvQuit(SimConnect sender, SIMCONNECT_RECV data)
        {
            labelConnectStatus.Text = "sim has exited";
            closeConnection();
            timerRequestData.Enabled = false;
        }
        #endregion
        #region MSFS2020 功能函数
        private void MSFS2020_SetAirplanePosition(double Altitude,
            double Latitude,
            double Longitude,
            double Pitch,
            double Bank,
            double Heading,
            uint OnGround,
            uint Airspeed)
        {
            SIMCONNECT_DATA_INITPOSITION Init;
            Init.Altitude = Altitude;
            Init.Latitude = Latitude;
            Init.Longitude = Longitude;
            Init.Pitch = Pitch;
            Init.Bank = Bank;
            Init.Heading = Heading;
            Init.OnGround = OnGround;
            Init.Airspeed = Airspeed;
            simconnect.SetDataOnSimObject(DEFINITIONS.Struct2,
                (uint)SIMCONNECT_SIMOBJECT_TYPE.USER,
                SIMCONNECT_DATA_SET_FLAG.DEFAULT,
                Init);
        }

        private void MSFS2020_SetNonATCObject(
            double Altitude,
            double Latitude,
            double Longitude,
            double Pitch,
            double Bank,
            double Heading,
            uint OnGround,
            uint Airspeed,
            string title)
        {
            SIMCONNECT_DATA_INITPOSITION Init;
            Init.Altitude = Altitude;
            Init.Latitude = Latitude;
            Init.Longitude = Longitude;
            Init.Pitch = Pitch;
            Init.Bank = Bank;
            Init.Heading = Heading;
            Init.OnGround = OnGround;
            Init.Airspeed = Airspeed;

            simconnect.AICreateNonATCAircraft(title, "N1001", Init, AIObject_REQUESTS.REQUEST_ADD_A320);
        }

        private void MSFS2020_SetDataOnSimObject(DEFINITIONS_WAYPOINT d, uint objectID, SIMCONNECT_DATA_WAYPOINT[] wp)
        {
            Object[] objv1 = new object[wp.Length];
            wp.CopyTo(objv1, 0);
            //label10.Text = objv1[0].ToString();
            simconnect.SetDataOnSimObject(d, objectID, SIMCONNECT_DATA_SET_FLAG.DEFAULT, objv1);
        }

        private void MSFS2020_RemoveAIObject(uint id, AIObject_REQUESTS eventID)
        {
            simconnect.AIRemoveObject(id, eventID);
        }
        private void MSFS2020_TimeInc()
        {
            simconnect.MapClientEventToSimEvent((Enum)Form1.EVENTS.KEY_CLOCK_HOURS_INC, "CLOCK_HOURS_INC");
            simconnect.TransmitClientEvent(0U, (Enum)Form1.EVENTS.KEY_CLOCK_HOURS_INC, 1, (Enum)Form1.NOTIFICATION_GROUPS.GROUP0, SIMCONNECT_EVENT_FLAG.GROUPID_IS_PRIORITY);
        }
        private void MSFS2020_TimeDec()
        {
            simconnect.MapClientEventToSimEvent((Enum)Form1.EVENTS.KEY_CLOCK_HOURS_DEC, "CLOCK_HOURS_DEC");
            simconnect.TransmitClientEvent(0U, (Enum)Form1.EVENTS.KEY_CLOCK_HOURS_DEC, 1, (Enum)Form1.NOTIFICATION_GROUPS.GROUP0, SIMCONNECT_EVENT_FLAG.GROUPID_IS_PRIORITY);
        }

        private void MSFS2020_HourSet(int hour)
        {
            simconnect.MapClientEventToSimEvent((Enum)Form1.EVENTS.KEY_CLOCK_HOURS_SET, "CLOCK_HOURS_SET");
            simconnect.TransmitClientEvent(0U, (Enum)Form1.EVENTS.KEY_CLOCK_HOURS_SET, (uint)hour, (Enum)Form1.NOTIFICATION_GROUPS.GROUP0, SIMCONNECT_EVENT_FLAG.GROUPID_IS_PRIORITY);
            label10.Text = hour.ToString();
        }
        private void MSFS2020_MinuteSet(int minute)
        {
            simconnect.MapClientEventToSimEvent((Enum)Form1.EVENTS.KEY_CLOCK_MINUTE_SET, "CLOCK_MINUTES_SET");
            simconnect.TransmitClientEvent(0U, (Enum)Form1.EVENTS.KEY_CLOCK_MINUTE_SET, (uint)minute, (Enum)Form1.NOTIFICATION_GROUPS.GROUP0, SIMCONNECT_EVENT_FLAG.GROUPID_IS_PRIORITY);
        }
        private void MSFS2020_TimeSet(int hour, int minute)
        {
            MSFS2020_HourSet(hour);
            MSFS2020_MinuteSet(minute);
        }


        #endregion

        #region 按键响应
        private void buttonConnect_Click(object sender, EventArgs e)
        {
            if (simconnect == null)
            {
                try
                {
                    simconnect = new Microsoft.FlightSimulator.SimConnect.SimConnect("ViewControl", base.Handle, 0x402, null, 0);
                    //simconnect.AddToDataDefinition()
                    setButtons(false, true);
                    initDataRequest();
                    timerRequestData.Enabled = true;
                }
                catch (COMException)
                {
                    labelConnectStatus.Text = "Unable to connect to sim";
                }
            }
            else
            {
                labelConnectStatus.Text = "Error - try again";
                closeConnection();
                setButtons(true, false);
                timerRequestData.Enabled = false;
            }
        }
        private void buttonDisconnect_Click(object sender, EventArgs e)
        {
            closeConnection();
            setButtons(true, false);
            timerRequestData.Enabled = false;
            /*
            textBox_latitude.Text = "";
            textBox_longitude.Text = "";
            textBox_trueheading.Text = "";
            textBox_groundaltitude.Text = "";
            label_DirNumber.Text = "";
            label_FileNumber.Text = "";*/
        }

        private void checkBoxTopWindow_CheckedChanged(object sender, EventArgs e)
        {
            if (checkBoxTopWindow.Checked == true) Form1.ActiveForm.TopMost = false;
            else Form1.ActiveForm.TopMost = false;
        }

        private void Form1_FormClosed(object sender, FormClosedEventArgs e)
        {
            closeConnection();
            timerRequestData.Enabled = false;
        }

        private void buttonCopy_Click(object sender, EventArgs e)
        {
            textBoxLon2.Text = textBoxLongitude.Text;
            textBoxLat2.Text = textBoxLatitude.Text;
            textBoxAlt2.Text = textBoxAltitude.Text;
            textBoxPit2.Text = textBoxPitch.Text;
            textBoxBnk2.Text = textBoxBank.Text;
            textBoxHDG2.Text = textBoxHeading.Text;
            //textBoxASPD2.Text =  textBoxAirspeed.Text;
        }

        private void buttonPosition_Click(object sender, EventArgs e)
        {
            MSFS2020_SetAirplanePosition(
                Convert.ToDouble(textBoxAlt2.Text),
                Convert.ToDouble(textBoxLat2.Text),
                Convert.ToDouble(textBoxLon2.Text),
                Convert.ToDouble(textBoxPit2.Text),
                Convert.ToDouble(textBoxBnk2.Text),
                Convert.ToDouble(textBoxHDG2.Text),
                Convert.ToUInt32(textBoxOnGround.Text),
                Convert.ToUInt32(textBoxASPD2.Text));
        }

        private void buttonTimeInc_Click_1(object sender, EventArgs e)
        {
            MSFS2020_TimeInc();
        }

        private void buttonTimeDec_Click_1(object sender, EventArgs e)
        {
            MSFS2020_TimeDec();
        }

        #endregion

        #region 其他函数
        private void closeConnection()
        {
            if (simconnect != null)
            {
                simconnect.Dispose();
                simconnect = null;
                labelConnectStatus.Text = "Connection closed";
            }
        }


        private void setButtons(bool bConnect, bool bDisconnect)
        {
            buttonConnect.Enabled = bConnect;
            buttonDisconnect.Enabled = bDisconnect;
        }

        private void timerRequestData_Tick(object sender, EventArgs e)
        {
            simconnect.RequestDataOnSimObjectType(DATA_REQUESTS.REQUEST_1, DEFINITIONS.Struct1, 0, SIMCONNECT_SIMOBJECT_TYPE.USER);
            labelDatastatus.Text = "Request sent...";
        }

        #endregion

        private void buttonSetObject_Click(object sender, EventArgs e)
        {
            if (checkBoxA320.Checked)
            {
                MSFS2020_SetNonATCObject(
                    3077,
                    43.432455,
                    83.391067,
                    0,
                    0,
                    265.7865,
                    1,
                    160,
                    "Airbus A320 Neo Asobo");
            }
            else
            {

            }
        }

        private void buttonPlaneSet_Click(object sender, EventArgs e)
        {
            MSFS2020_SetNonATCObject(
                    3077,
                    43.432455,
                    83.391067,
                    0,
                    0,
                    265.7865,
                    1,
                    0,
                    "Airbus A320 Neo Asobo");
        }

        private void buttonPlaneStart_Click(object sender, EventArgs e)
        {
            simconnect.AddToDataDefinition(DEFINITIONS_WAYPOINT.WAYPOINT_TAKEOFF, "AI WAYPOINT LIST", "number", SIMCONNECT_DATATYPE.WAYPOINT, 0.0f, SimConnect.SIMCONNECT_UNUSED);



            SIMCONNECT_DATA_WAYPOINT[] waypoints = new SIMCONNECT_DATA_WAYPOINT[2];



            waypoints[0].Flags = (uint)SIMCONNECT_WAYPOINT_FLAGS.SPEED_REQUESTED;
            waypoints[0].ktsSpeed = 100;
            waypoints[0].Latitude = 10;
            waypoints[0].Longitude = 20;
            waypoints[0].Altitude = 1000;

            waypoints[1].Flags = (uint)SIMCONNECT_WAYPOINT_FLAGS.SPEED_REQUESTED;
            waypoints[1].ktsSpeed = 150;
            waypoints[1].Latitude = 11;
            waypoints[1].Longitude = 21;
            waypoints[1].Altitude = 2000;



            Object[] objv = new Object[waypoints.Length];
            waypoints.CopyTo(objv, 0);



            simconnect.SetDataOnSimObject(DEFINITIONS_WAYPOINT.WAYPOINT_TAKEOFF, A320ID, SIMCONNECT_DATA_SET_FLAG.DEFAULT, objv);
            /*if (A320ID != 0)
            {
                SIMCONNECT_DATA_WAYPOINT[] wp = new SIMCONNECT_DATA_WAYPOINT[1];
                wp[0].Flags = (uint)SIMCONNECT_WAYPOINT_FLAGS.SPEED_REQUESTED;
                wp[0].Altitude = 3043;
                wp[0].Latitude = 43.431401;
                wp[0].Longitude = 83.371510;
                wp[0].ktsSpeed = 140;

                wp[1].Flags = (uint)SIMCONNECT_WAYPOINT_FLAGS.COMPUTE_VERTICAL_SPEED;
                wp[1].Altitude = 5000;
                wp[1].Latitude = 43.426872;
                wp[1].Longitude = 83.286283;
                wp[1].ktsSpeed = 190;

                Object[] objv = new Object[wp.Length];
                wp.CopyTo(objv, 0);



                simconnect.SetDataOnSimObject(DEFINITIONS_WAYPOINT.WAYPOINT_TAKEOFF, A320ID, SIMCONNECT_DATA_SET_FLAG.DEFAULT, objv);

                //MSFS2020_SetDataOnSimObject(DEFINITIONS_WAYPOINT.WAYPOINT_TAKEOFF, A320ID, wp);
            }*/
        }

        private void button1_Click(object sender, EventArgs e)
        {
            textBoxLon2.Text = (83.5639571).ToString();
            textBoxLat2.Text = (43.4408350).ToString();
            textBoxAlt2.Text = (6263.7721).ToString();
            textBoxPit2.Text = (0).ToString();
            textBoxBnk2.Text = (0).ToString();
            textBoxHDG2.Text = (270).ToString();
            textBoxASPD2.Text = (160).ToString();
        }

        int timeElapse = 0;
        int hourStart = 5;
        int hourEnd = 21;
        int hourInterval = 1;
        int minuteStart = 0;
        int minuteEnd = 60;
        int minuteInterval = 15;
        int hour = 0;
        int minute = 0;
        double LonStart = 83.391067058;
        double LatStart = 43.432455394;
        double LonEnd = 83.375894828;
        double LatEnd = 43.431638470;
        int posLimit = 15;
        int time = 0;
        [DllImport("user32")]
        private static extern int mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
        const int MOUSEEVENTF_MOVE = 0x0001;
        //模拟鼠标左键按下 
        const int MOUSEEVENTF_LEFTDOWN = 0x0002;
        //模拟鼠标左键抬起 
        const int MOUSEEVENTF_LEFTUP = 0x0004;
        //模拟鼠标右键按下 
        const int MOUSEEVENTF_RIGHTDOWN = 0x0008;
        //模拟鼠标右键抬起 
        const int MOUSEEVENTF_RIGHTUP = 0x0010;
        //模拟鼠标中键按下 
        const int MOUSEEVENTF_MIDDLEDOWN = 0x0020;
        //模拟鼠标中键抬起 
        const int MOUSEEVENTF_MIDDLEUP = 0x0040;
        //标示是否采用绝对坐标 
        const int MOUSEEVENTF_ABSOLUTE = 0x8000;
        //模拟鼠标滚轮滚动操作，必须配合dwData参数
        const int MOUSEEVENTF_WHEEL = 0x0800;
        

        [DllImport("user32.dll", EntryPoint = "FindWindow")]
        private extern static IntPtr FindWindow(string lpClassName, string lpWindowName);
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        private void button2_Click(object sender, EventArgs e)
        {
            hour = hourStart;
            minute = minuteStart;
            if (timerDynamicCapture.Enabled)
            {
                timerDynamicCapture.Stop();
            }
            else
            {
                timerDynamicCapture.Start();
            }
            string gameName = "Microsoft Flight Simulator - 1.7.12.0";
            IntPtr ParenthWnd = FindWindow(null, gameName);
            SetForegroundWindow(ParenthWnd);
            //IntPtr renderdoc = IntPtr.Zero;
            //DllGetClassObject(RENDERDOC_Version.eRENDERDOC_API_Version_1_3_0, this.Handle);
            int i = 0;
            //double a = 0.00001;
            //double b = 0.0000008;
            double a = 0.0001;
            double b = 0.000008;
            double m = Convert.ToDouble(textBoxHeading.Text);
            double k = (m * (MathF.PI)) / 180;
            float v = MathF.Cos(x: (float)k);
            float n = MathF.Sin(x: (float)k);
            for (i = 0; i <= 10; i++)
            {



                /*MSFS2020_SetAirplanePosition(
                                Convert.ToDouble(textBoxAlt2.Text),
                                Convert.ToDouble(textBoxLat2.Text)+ a * i* flag1,
                                Convert.ToDouble(textBoxLon2.Text) - a * i* flag2,
                                Convert.ToDouble(textBoxPit2.Text),
                                Convert.ToDouble(textBoxBnk2.Text),
                                Convert.ToDouble(textBoxHDG2.Text),
                                Convert.ToUInt32(textBoxOnGround.Text),
                                Convert.ToUInt32(textBoxASPD2.Text));*/

                MSFS2020_SetAirplanePosition(
                                Convert.ToDouble(textBoxAltitude.Text),
                                Convert.ToDouble(textBoxLatitude.Text) + a * v * i,
                                Convert.ToDouble(textBoxLongitude.Text) + a * n * i,
                                Convert.ToDouble(textBoxPitch.Text),
                                Convert.ToDouble(textBoxBank.Text),
                                Convert.ToDouble(textBoxHeading.Text),
                                Convert.ToUInt32(textBoxOnGround.Text),
                                Convert.ToUInt32(textBoxASPD2.Text));

                Thread.Sleep(120);
            
            SendKeys.Send("{F12}");
            }
            //sc.CaptureScreenToFile("E:\\test.jpg", ImageFormat.Jpeg);
            //fetchScreen();
        }

        private void button3_Click(object sender, EventArgs e)
        {
            int hour = Convert.ToInt16(textBoxHour.Text.ToString());
            int minute = Convert.ToInt16(textBoxMinute.Text.ToString());
            MSFS2020_TimeSet(hour, minute);
        }

        /// <summary>
        /// 定时器相应函数，用于截取飞机图片
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void timerDynamicCapture_Tick(object sender, EventArgs e)
        {
            timeElapse += 100;
            if(timeElapse<=20000 && timeElapse % 500 == 0)
            {
                sc.CaptureScreenToFile("E:\\Data\\" + textBoxWeather.Text.ToString() + "_" + hour.ToString() + "_" + minute.ToString() + "_" + timeElapse.ToString() + ".jpg", ImageFormat.Jpeg);
            }
        }

        /// <summary>
        /// 定时器相应函数，用于设置飞机在不同时刻动态出发
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void timerDynamicPlaneSet_Tick(object sender, EventArgs e)
        {

            if(timeElapse >= 20000)
            {
                minute = minute + minuteInterval;
                if(minute >= minuteEnd)
                {
                    hour = hour + hourInterval;
                    minute = minute - minuteEnd;
                }
                if(hour >= hourEnd)
                {
                    timerDynamicCapture.Stop();
                    timerDynamicPlaneSet.Stop();
                    return;
                }
            }

            if(timeElapse >= 20000 || timeElapse == 0)
            {
                timeElapse = 100;
                MSFS2020_TimeSet(hour, minute);
                MSFS2020_SetNonATCObject(
                    3077,
                    43.432455,
                    83.391067,
                    0,
                    0,
                    265.7865,
                    1,
                    160,
                    "Airbus A320 Neo Asobo");
                return;
            }
        }

        private void button4_Click(object sender, EventArgs e)
        {
            hour = hourStart;
            minute = minuteStart;
            if (timerStaticPlaneSet.Enabled)
            {
                timerStaticPlaneSet.Stop();
            }
            else
            {
                timerStaticPlaneSet.Start();
            }
        }



        private void button6_Click(object sender, EventArgs e)
        {

            int i = 0;
            //double a = 0.00001;
            //double b = 0.0000008;
            double a = 0.0001;
            double b = 0.000008;
            double m = Convert.ToDouble(textBoxHeading.Text);
            double k = (m * (MathF.PI)) / 180;
            float v = MathF.Cos(x: (float)k);
            float n = MathF.Sin(x: (float)k);
            for (i = 0; i <= 10; i++)
            {



                /*MSFS2020_SetAirplanePosition(
                                Convert.ToDouble(textBoxAlt2.Text),
                                Convert.ToDouble(textBoxLat2.Text)+ a * i* flag1,
                                Convert.ToDouble(textBoxLon2.Text) - a * i* flag2,
                                Convert.ToDouble(textBoxPit2.Text),
                                Convert.ToDouble(textBoxBnk2.Text),
                                Convert.ToDouble(textBoxHDG2.Text),
                                Convert.ToUInt32(textBoxOnGround.Text),
                                Convert.ToUInt32(textBoxASPD2.Text));*/

                MSFS2020_SetAirplanePosition(
                                Convert.ToDouble(textBoxAltitude.Text),
                                Convert.ToDouble(textBoxLatitude.Text) + a * v*i,
                                Convert.ToDouble(textBoxLongitude.Text) + a * n*i,
                                Convert.ToDouble(textBoxPitch.Text),
                                Convert.ToDouble(textBoxBank.Text),
                                Convert.ToDouble(textBoxHeading.Text),
                                Convert.ToUInt32(textBoxOnGround.Text),
                                Convert.ToUInt32(textBoxASPD2.Text));

                Thread.Sleep(120);
            }
        }

        private void buttonPlaneRemove_Click(object sender, EventArgs e)
        {
            if (A320ID != 0)
            {
                MSFS2020_RemoveAIObject(A320ID, AIObject_REQUESTS.REQUEST_REMOVE_A320);
            }
        }

        private void timerStaticPlaneSet_Tick(object sender, EventArgs e)
        {
            if(A320ID != 0)
            {
                label10.Text = "A320ID is not 0";
                sc.CaptureScreenToFile("E:\\Data\\" + textBoxWeather.Text.ToString() + "_" + hour.ToString() + "_" + minute.ToString() + "_" + timeElapse.ToString() + ".jpg", ImageFormat.Jpeg);
                MSFS2020_RemoveAIObject(A320ID, AIObject_REQUESTS.REQUEST_REMOVE_A320);
                A320ID = 0;
                return;
            }
            timeElapse += 1;
            if(timeElapse == posLimit + 1)
            {
                timeElapse = 0;
                minute = minute + minuteInterval;
                if (minute >= minuteEnd)
                {
                    hour = hour + hourInterval;
                    minute = minute - minuteEnd;
                }
                if (hour >= hourEnd)
                {
                    timerStaticPlaneSet.Stop();
                }
            }

            

            MSFS2020_TimeSet(hour, minute);
            MSFS2020_SetNonATCObject(
                3077,
                LatStart + (LatEnd - LatStart) / posLimit * timeElapse,
                LonStart + (LonEnd - LonStart) / posLimit * timeElapse,
                0,
                0,
                265.7865,
                1,
                0,
                "Airbus A320 Neo Asobo");
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        private void textBoxLongitude_TextChanged(object sender, EventArgs e)
        {

        }

        private void button5_Click(object sender, EventArgs e)
        {
            //更改天气按钮

            simconnect.WeatherCreateStation(DATA_REQUESTS.REQUEST_1, "ZWNL", "WeaContro", 0, 0, 100);
            simconnect.WeatherSetObservation(0, "ZWNL 27007KT 15SM R01/1000FT +VCTSRA 17/13");

        }
    }
}
