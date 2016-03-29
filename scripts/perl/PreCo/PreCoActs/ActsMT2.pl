#! /usr/bin/perl -w
# ActsMT2.pl -- MySQL:ECM_Acts_Base:localhost
# schreibt die Anzahl der Byz-ReprŠsentanten in ein Feld BZ in $target
# schreibt die Anzahl der Byz-Hss., die an einer variierten Stelle einer Variante eindeutig zugeordnet werden kšnnen, in ein Feld BZdef in $target2
# ermittelt an jeder variierten Stelle die Byz-Lesart und markiert sie mit BYZ = 'B' in der Rdg-Tabelle, wenn sie nach den in 'ArbeitsablaufCBGMApg' formulierten Kriterien bestimmt werden kann.
# Vorlage von Klaus Wachtel, bearbeitet von Volker KrŸger

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_Base:localhost";	# data source 
my $user_name = getUsername();						# user name
my $password = getPassword();						# password


my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my $chn = 6;
### INTERAKTIVER AUFRUF DES SKRIPTS ###
if(1) # Interaktiven Aufruf ein- bzw. ausschalten
{
    print "Bitte Kapitel eingeben: ";
    chomp($chn = <STDIN>);
}
### INTERAKTIV ENDE ###
my $chnstr;
if ($chn < 10)
{
	$chnstr = '0'.$chn;
} else {
	$chnstr = $chn;
}

#my $db = 'ECM_Acts_Base';
my $target1 = '`ECM_Acts_Base`.`05'.$chnstr.'VP`';
my $target2 = '`ECM_Acts_Base`.`05'.$chnstr.'Rdg`';
my $source = '`ECM_Acts_Base`.`05'.$chnstr.'Witn`';

#Liste der Byz-ReprŠsentanten
my @byzlist = (300010, 300180, 300350, 303300, 303980, 304240, 312410);

my ($byz, $ary, @ary, $sth, $bzdef);

#BZdef: Anzahl der Byz-ReprŠsentanten, die an der jeweiligen variierten Stelle Text haben.
#BZ: Anzahl der Byz-ReprŠsentanten, die die jeweilige Variante bezeugen.
#BYZ: markiert die nach unseren Regeln identifizierte Mehrheitslesart.

#Da dieses Script die Felder BZ, BZdef u. BYZ fŸllt, sorge ich zunŠchst dafŸr, dass in ihnen aus frŸheren DurchgŠngen nichts steht.

$dbh->do ("UPDATE $target1 SET BZdef = 0");
$dbh->do ("UPDATE $target2 SET BZ = 0, BZdef = 0, BYZ = ''");

#Ich gehe die Liste der Byz-ReprŠsentanten durch und 
#setze BZdef +1 an den Stellen, an denen die jeweilige Handschrift Text hat,
#setze BZ +1 bei den Varianten, die die jeweilige Handschrift bezeugt.

#FŸr jedes Element vom @byzlist...
foreach $byz(@byzlist)
{
	#...wŠhle ich die Varianten aus, die von der jeweiligen Handschrift bezeugt werden
	$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ FROM $source WHERE HSNR = $byz" );
	$sth->execute();

	#Dann gehe ich die Auswahl durch und prŸfe, ob die DatensŠtze die Bedingungen erfŸllen, die BZdef+1 oder BZ+1 erlauben.
	while (@ary = $sth->fetchrow_array())
	{
		#Wenn die Handschrift bei zz, zv, zu oder zw steht...
		if ($ary[2] eq 'zz' or $ary[2] eq 'zv' or $ary[2] eq 'zu' or $ary[2] eq 'zw')
		{
			#...gehe ich ohne etwas zu tun zum nŠchsten Datensatz.
			next;
		
		#Wenn die Handschrift eine Variante bezeugt, setze ich BZdef und BZ +1.
		} else {
			$dbh->do ("UPDATE $target1 SET BZdef = BZdef+1 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1]");
			$dbh->do ("UPDATE $target2 SET BZ = BZ+1 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND LABEZ = '$ary[2]'");
		}
	}
}

#Ich wŠhle die Varianten aus, bei denen BZ>1, denn nur sie kommen Ÿberhaupt als Mehrheitslesarten infrage.
$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ FROM $target2 WHERE BZ > 0" );
$sth->execute();

#Ich Ÿbertrage die BZdef-Werte aus 0501VP zu den Varianten, die von mindestens einem Byz-ReprŠsentanten bezeugt werden, in die Variantentabelle
while (@ary = $sth->fetchrow_array())
{
	$bzdef = $dbh->selectrow_array ("SELECT BZdef FROM $target1 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1]");
	
	$dbh->do ("UPDATE $target2 SET BZdef = $bzdef WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND LABEZ LIKE '$ary[2]'");
}

#Wo BZdef und BZ Ÿbereinstimmen (und >0 sind) ODER wo BZdef-1=BZ, ist die Mehrheitslesart bestimmt und BYZ wird gleich 'B' gesetzt.

$dbh->do ("UPDATE $target2 SET BYZ = 'B' WHERE (BZdef = BZ AND BZdef > 0) OR BZ = BZdef-1");

#Jetzt sind noch die Mehrheitslesarten an den Stellen zu bestimmen, an denen hšchstens zwei Byz-ReprŠsentanten mit unterschiedlichen Lesarten von der Mehrheit abweichen. 
#Das kšnnen nur Stellen sein, an denen einzelne Byz-ReprŠsentanten abweichen.

#Daher ziehe ich zunŠchst die DatensŠtze mit BZ = 1 heraus...
$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, BZ, BZdef FROM $target2 WHERE BZ = 1" );
$sth->execute();

#...und gehe einen nach dem anderen durch.
while (@ary = $sth->fetchrow_array())
{
	#Ich teste, ob an der Stelle mit der einzelnen Abweichung die Mehrheitslesart schon identifiziert ist.
	my $testvar = $dbh->selectrow_array ("SELECT BYZ FROM $target2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND BYZ LIKE 'B'");
	
	#Wenn ja,
	if (defined($testvar))
	{
		#ist die Sache erledigt und ich gehe zum nŠchsten Datensatz.
		undef $testvar; #Variable muss fŸr den nŠchsten Durchgang leer sein.
		next;
		
	#Wenn nicht,
	} else {
		#prŸfe ich, ob es noch einen (und nur einen) weiteren Datensatz mit derselben Adresse und BZ = 1 gibt. Das wŸrde bedeuten, dass es insgesamt 3 DatensŠtze mit derselben Adresse gibt und 2 von ihnen BZ=1 haben. Der dritte enthŠlt die Mehrheitslesart.
		
		#Gibt es drei DatensŠtze mit derselben Adresse?
		my $testzahl1 = $dbh->selectrow_array ("SELECT COUNT(*) FROM $target2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1]");
		if ($testzahl1==3)
		{
			#Wenn ja, haben 2 von ihnen BZ>1?
			my $testzahl2 = $dbh->selectrow_array ("SELECT COUNT(*) FROM $target2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND BZ>1");
			if ($testzahl2 > 1)
			{
				#Wenn ja, ist die Mehrheitslesart nach unseren Regeln nicht bestimmbar und ich gehe zum nŠchsten Datensatz.
				undef $testzahl1;
				undef $testzahl2; 
				next;
			#Wenn nicht, ist die Variante mit BZ>1 die Mehrheitslesart und muss mit BYZ = 'B' markiert werden.
			} else {
				undef $testzahl1;
				undef $testzahl2; 
				$dbh->do ("UPDATE $target2 SET BYZ = 'B' WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND BZ>1");
			}
		
		#Wenn es mehr als 3 DatensŠtze mit derselben Adresse gibt, ist die Mehrheitslesart nach unseren Regeln nicht bestimmbar und ich gehe zum nŠchsten Datensatz.
		} else {
			undef $testzahl1;
			next;
		}
	}
}


$sth->finish ();

$dbh->disconnect ();

exit (0);
