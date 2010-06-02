package org.tamaki.net
{
	import flash.events.*;
	import flash.net.Socket;
	import flash.utils.*;
	
	import mx.controls.*;
	
	import org.tamaki.events.*;
	
	public class MySocket extends Socket {

		public function MySocket(host:String = "www.avfun001.org", port:uint = 1818){			
			super(host, port);	
			addEventListener(Event.CONNECT, onConnect);			
			addEventListener(Event.CLOSE, onClose);			
			addEventListener(IOErrorEvent.IO_ERROR, onError);			
			addEventListener(ProgressEvent.SOCKET_DATA, onResponse);			
		}

		private function onConnect(e:Event):void{
			trace('connected');
			this.dispatchEvent(new LoadEvent(LoadEvent.SOCKET_CONNECTED,""));
		}

		private function onClose(e:Event):void{			
			trace('closed');
		}

		private function onError(e:IOErrorEvent):void{			
			trace('connection error');			
		}

		private function onResponse(e:ProgressEvent):void{
			trace('datareceived');
			var str:String = readUTFBytes(bytesAvailable);
			this.dispatchEvent(new LoadEvent(LoadEvent.SUB_RECEIVED,str));
		}

		public function send(str:String):void{
			writeUTFBytes(str);
			flush();
		}

	}
}
