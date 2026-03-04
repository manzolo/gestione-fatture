import java.io.File;
import java.io.FileInputStream;
import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;

public class ValidatoreXml730 
{
	public static void main(String[] args) throws Exception
	{
		// CONFIGURARE I PAREMETRI
		// primo parametro il path del file xsd
		// secondo parametro il path del file xml da validare
		validateXMLSchema("d:/730_precompilata.xsd", "d:/prove730/anno_2020_c_fisc_codificati.xml");
	}

	public static boolean validateXMLSchema(String xsdPath, String xmlPath)
	{
		try
		{
			SchemaFactory factory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
			Schema schema = factory.newSchema(new File(xsdPath));
			Validator validator = schema.newValidator();
			validator.validate(new StreamSource(new File(xmlPath)));
		} 
		catch (Exception e) 
		{
			e.printStackTrace();
			System.out.println("Exception: "+e.getMessage());
			System.out.println(xmlPath + " -> CONTROLLO KO"); 

			return false;
		}

		System.out.println(xmlPath + " -> CONTROLLO OK"); 

		return true;
	}

	public static byte[] getByteFileToFileLocale(String fileInput) throws Exception
	{
		FileInputStream fileInputStream = null;
		byte[] file;
		byte[] fileTMP = new byte[6000000];
		byte[] buffer = new byte[65*1024];
		int readedByte = 0;
		int dimensione = 0;

		try
		{
			fileInputStream = new FileInputStream(fileInput); 

			while((readedByte = fileInputStream.read(buffer, 0, buffer.length))>=0)
			{
				for (int i=dimensione, j=0;i<(dimensione + readedByte);i++,j++)
				{
					fileTMP[i] = buffer[j];	
				}

				dimensione = dimensione + readedByte;
			}

			file = new byte[dimensione];

			for (int i=0;i<dimensione;i++) 
			{
				file[i] = fileTMP[i];
			}
		}
		finally
		{
			if(fileInputStream!=null)
			{
				try
				{
					fileInputStream.close();
				}
				catch(Exception eignore)
				{};
			}
		}

		return file;
	}
}
