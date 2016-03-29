#! /usr/bin/perl -w
# WitGen.pl -- MySQL:CBGM_CL2_Base:ivv7srv16.uni-muenster.de
# WitGen-Tabellen aus <n>Witn-Tabellen erzeugen u. entspr. zu LocStemEd erweitern
# Vorlage von Klaus Wachtel, weiter bearbeitet von Volker KrŸger

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_Base:localhost";   # data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

### AKTUELL ZU BEARBEITENDES BUCH UND KAPITEL ###
my $book = '05';
my $chap = '01';

### INTERAKTIVER AUFRUF DES SKRIPTS ###
if(1) # Interaktiven Aufruf ein- bzw. ausschalten
{
    print "Bitte Nummer des neutestamentlichen Buches eingeben (zweistellig): ";
    chomp($book = <STDIN>); # Zeilenumbruch entfernen mit chomp()
    print "Bitte Kapitel eingeben (zweistellig): ";
    chomp($chap = <STDIN>);
}
### INTERAKTIV ENDE ###

my $source11 = '`VarGenAtt_Act`.`LocStemEdAct'.$chap.'`';
my $source12 = '`VarGenAtt_Act`.`VarGenAttAct'.$chap.'`';
my $source2 = '`ECM_Acts_Base`.`'.$book.$chap.'Witn`';
my $target = '`ECM_Acts_Base`.`'.$book.$chap.'WitGen`';

my ($sth, @ary, $ary, $q1);

### NEUE ERGEBNISTABELLE ANLEGEN ###
$dbh->do ("DROP TABLE IF EXISTS $target;");
	$dbh->do ("CREATE  TABLE  $target (  
	 `ANFADR` int( 11  )  default NULL ,
	 `ENDADR` int( 11  )  default NULL ,
	 `LABEZ` varchar( 2  )  collate utf8_unicode_ci  default NULL ,
	 `HSNR` int( 6  )  default NULL
	  ) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");
$dbh->do ("INSERT INTO $target SELECT ANFADR, ENDADR, LABEZ, HSNR FROM $source2 WHERE 1");
$dbh->do ("ALTER TABLE $target ADD `LABNEU` varchar( 2  ), ADD `Q1` varchar( 2  ), ADD `Q2` varchar( 2  ), ADD `CHECK` varchar( 1  ) ;");
$dbh->do ("ALTER TABLE $target ADD INDEX  (`ANFADR`,`ENDADR`)");

#### LocStemEd-Tabelle + VarGenAtt abfragen ####
$sth = $dbh->prepare ("SELECT a.`BEGADR`, a.`ENDADR`, a.`VARID`, a.`VARNEW`, a.`S1`, a.`S2`, b.`MS` FROM $source11 a, $source12 b 
        WHERE a.`BEGADR` = b.`BEGADR` AND a.`ENDADR` = b.`ENDADR` AND a.`VARID` = b.`VARID` AND a.`VARNEW` = b.`VARNEW`; "); 
$sth->execute();

#0 BEGADR, 1 ENDADR, 2 VARID, 3 VARNEW, 4 S1, 5 S2, 6 MS(=HSNR)
	
while (@ary = $sth->fetchrow_array())
{
	my $cmd = "UPDATE $target SET `LABNEU` = '$ary[3]', `Q1` = '$ary[4]', `Q2` = '$ary[5]' WHERE `ANFADR` = $ary[0] AND `ENDADR` = $ary[1] AND `LABEZ` LIKE '$ary[2]' AND `HSNR` = '$ary[6]'; ";
	#print "$cmd\n";
	$dbh->do ($cmd);
}

$dbh->do ("UPDATE $target SET `LABNEU` = `LABEZ` WHERE `LABEZ` LIKE 'zz' OR `LABEZ` LIKE 'zx' OR 
			`LABEZ` LIKE 'zw' OR `LABEZ` LIKE 'zv' OR `LABEZ` LIKE 'zu' ; ");

$sth->finish ();

$dbh->disconnect ();

exit (0);
