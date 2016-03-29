#! /usr/bin/perl -w
# PortCBGMInfo.pl 
# kopiert die genealogische Informationen von einer Phase zur naechsten. 
# volker.krueger@uni-muenster.de

# Splitts muessen nur dort uebertragen werden, wo sich der Apparat nicht geaendert hat. 
# Hat sich der Apparat geaendert, d.h. gibt es in der neuen Phase fuer eine Adresse keine
# Entsprechung in der vorhergehenden Phase, so werden die Defaultwerte eingetragen. 
# Zuerst muss festgestellt werden, wo Splitts oder Zusammenlegungen stattgefunden haben. 
# Dann werden diese Lesarten geloescht und aus der vorhergehenden Phase kopiert.

# Stellen mit geänderter Leitzeile werden zunächst einfach übergangen.

# Defaultwerte eintragen, wenn eine variierte Stelle mit gleicher numerischer Adresse
# mehr Lesarten als in der vorhergehenden Phase hat,
# die nicht nur versionell bezeugt sind. 

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:VarGenAtt_Act:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 0, PrintError => 0, mysql_enable_utf8 => 1 });

### Quell- und Zieldatenbank eintragen ###
my $source_db = 'VarGenAtt_ActPh2';
my $target_db = 'VarGenAtt_ActPh3';

### Chapter Number von Kommandozeilenparameter übernommen ###
my $chn = $ARGV[0];
my $chnstr = '';
if ($chn < 10)
{
	$chnstr = '0'.$chn;	#HERE
} else {
	$chnstr = $chn;
}
my $cmd = ''; # SQL commands
my ($sth, @result, $result, $sth2, @res2, $res2, $sth3, @res3, $res3, $sth4);
my ($begadr, $endadr, $varid);

	### Zunächst das Spezielle ###
	### Suche Splitts und Zusammenlegungen in der Quelltabelle ###
	$cmd  = "select distinct begadr, endadr, varid from `".$source_db."`.`LocStemEdAct".$chnstr."` ";#+distinct -varnew 20140520
	$cmd .= "where varnew like '%1' ";
	$cmd .= "or varnew like '%2' ";
	$cmd .= "or varnew like '%3' ";
	$cmd .= "or varnew like '%4' ";
	$cmd .= "or varnew like '%5' ";
	$cmd .= "or varnew like '%6' ";
	$cmd .= "or varnew like '%7' ";
	$cmd .= "or varnew like '%8' ";
	$cmd .= "or varnew like '%9' ";
	$cmd .= "or varnew like '%!' "; # Zusammenlegungen
	$sth = $dbh->prepare ($cmd);
	$sth->execute ();
	while (@result = $sth->fetchrow_array())
	{
		# Gehört diese Stelle zur Tabelle der geänderten Leitzeilen?
		my $begadr = $result[0];
		my $endadr = $result[1];
		$cmd  = "select count(*) from `Apparat`.`Leitzeile` ";
		$cmd .= "where anfadr = $begadr ";
		$cmd .= "and endadr = $endadr; ";
		$sth3 = $dbh->prepare($cmd);
		$sth3->execute ();
		@res3 = $sth3->fetchrow_array ();
		my $count = $res3[0];
		if ($count gt 0) {
			next;
		}
		
		### Suche geaenderte Adressen ###
		$cmd  = "select count(*) from `".$target_db."`.`LocStemEdAct".$chnstr."` ";
		$cmd .= "where begadr =  $result[0] ";
		$cmd .= "and endadr   =  $result[1] ";
		$cmd .= "and varid    = '$result[2]' ";
		$cmd .= "and varnew like '$result[2]%'; ";
		#print $cmd."\n";
		$sth2 = $dbh->prepare ($cmd);
		$sth2->execute ();
		@res2 = $sth2->fetchrow_array ();
		$count = $res2[0];
		#print $count."\n";
		if ($count gt 0) # copy data
		{
			# LocStemEd
			# a) delete statement
			$cmd  = "delete from `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "where begadr =  $result[0] ";
			$cmd .= "and endadr   =  $result[1] ";
			$cmd .= "and varid    = '$result[2]' ";
			$dbh->do ($cmd);
			# b) insert statement
			# drop id temporarily
			$cmd  = "alter table `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "drop id; ";
			$dbh->do ($cmd);
			# insert
			$cmd  = "insert into `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "select varid, varnew, s1, s2, prs1, prs2, begadr, endadr, ";
			$cmd .= "`check`, check2, w from `".$source_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "where begadr =  $result[0] ";
			$cmd .= "and endadr   =  $result[1] ";
			$cmd .= "and varid    = '$result[2]' ";
			$dbh->do ($cmd);
			# add id field again
			$cmd  = "alter table `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "add id int auto_increment primary key first; ";
			$dbh->do ($cmd);
			# VarGenAtt
			# a) delete statement
			$cmd  = "delete from `".$target_db."`.`VarGenAttAct".$chnstr."` ";
			$cmd .= "where begadr =  $result[0] ";
			$cmd .= "and endadr   =  $result[1] ";
			$cmd .= "and varid    = '$result[2]' ";
			$dbh->do ($cmd);
			# b) insert statement
			$cmd  = "insert into `".$target_db."`.`VarGenAttAct".$chnstr."` ";
			$cmd .= "select * from `".$source_db."`.`VarGenAttAct".$chnstr."` ";
			$cmd .= "where begadr =  $result[0] ";
			$cmd .= "and endadr   =  $result[1] ";
			$cmd .= "and varid    = '$result[2]' ";
			$dbh->do ($cmd);
		}
	}

# Passages erfragen:
$cmd = "select begadr, endadr, varid from `$target_db`.`LocStemEdAct".$chnstr."`; ";
$sth = $dbh->prepare ($cmd);
$sth->execute ();
while (@result = $sth->fetchrow_array())
{
	my ($begadr, $endadr);
	$begadr = $result[0];
	$endadr = $result[1];
	# Gibt es mehr Varianten als in der vorhergehenden Phase
	# Wenn ja, dann belasse die Default-Werte und gehe gleich
	# zur nächsten Passage weiter. 
	my ($count_var_2, $count_var_3);
	$count_var_2 = $dbh->selectrow_array ("select count(varid) from `$source_db`.`LocStemEdAct".$chnstr."` where begadr = $begadr and endadr = $endadr; ");
	$count_var_3 = $dbh->selectrow_array ("select count(varid) from `$target_db`.`LocStemEdAct".$chnstr."` where begadr = $begadr and endadr = $endadr; ");
	if ($count_var_2 ne $count_var_3) {
		next;
	}
	
	### Danach das Allgemeine ###
	### Update der unveraenderten Adressen ###
	### a) Update LocStem-Tabellen ###
	$cmd  = "update `".$source_db."`.`LocStemEdAct".$chnstr."` a, `".$target_db."`.`LocStemEdAct".$chnstr."` b ";
	$cmd .= "set b.`check` = a.`check`, ";
	$cmd .= "b.`check2` = a.`check2`, ";
	$cmd .= "b.`w` = a.`w`, ";
	$cmd .= "b.`s1` = a.`s1` where ";
	$cmd .= "b.`begadr` = $begadr and ";
	$cmd .= "b.`endadr` = $endadr and ";
	$cmd .= "b.`begadr` = a.`begadr` and ";
	$cmd .= "b.`endadr` = a.`endadr` and ";
	$cmd .= "b.`varid`  = a.`varid` and ";
	$cmd .= "b.`varnew` = a.`varnew`; ";
	$dbh->do ($cmd);
	
	### b) Update Bezeugungs-Tabellen ###
	$cmd  = "update `".$source_db."`.`VarGenAttAct".$chnstr."` a, `".$target_db."`.`VarGenAttAct".$chnstr."` b ";
	$cmd .= "set b.`s1` = a.`s1`, ";
	$cmd .= "b.`varnew` = a.`varnew` where ";
	$cmd .= "b.`begadr` = $begadr and ";
	$cmd .= "b.`endadr` = $endadr and ";
	$cmd .= "b.`begadr` = a.`begadr` and ";
	$cmd .= "b.`endadr` = a.`endadr` and ";
	$cmd .= "b.`varid`  = a.`varid` and ";
	$cmd .= "b.`varnew` = a.`varnew`; ";
	$dbh->do ($cmd);
	
	### c) Update Lesarten-Tabellen ###
	$cmd  = "update `".$source_db."`.`RdgAct".$chnstr."` a, `".$target_db."`.`RdgAct".$chnstr."` b ";
	$cmd .= "set b.`al` = a.`al`, ";
	$cmd .= "b.`zv` = a.`zv` where ";
	$cmd .= "b.`anfadr` = $begadr and ";
	$cmd .= "b.`endadr` = $endadr and ";
	$cmd .= "b.`anfadr` = a.`anfadr` and ";
	$cmd .= "b.`endadr` = a.`endadr` and ";
	$cmd .= "b.`labez`  = a.`labez`  and ";
	$cmd .= "b.`labezsuf` = a.`labezsuf`; ";
	$dbh->do ($cmd);

	### Schließlich suche neue Adressen ohne Entsprechung in der vorhergehende Phase
	$cmd  = "select distinct begadr, endadr, varid ";
	$cmd .= "from `".$target_db."`.`LocStemEdAct".$chnstr."` ";
	$cmd .= "order by begadr, endadr desc, varid; ";
	$sth4 = $dbh->prepare($cmd) or die "Caught error: $dbh->errstr";
	my $void = $sth4->execute() or die "Caught error: $sth4->errstr";
	while (($begadr, $endadr, $varid) = $sth4->fetchrow_array())
	{
		# Gehört diese Stelle zur Tabelle der geänderten Leitzeilen?
		$cmd  = "select count(*) from `Apparat`.`Leitzeile` ";
		$cmd .= "where anfadr = $begadr ";
		$cmd .= "and endadr = $endadr; ";
		$sth3 = $dbh->prepare($cmd);
		$sth3->execute ();
		@res3 = $sth3->fetchrow_array ();
		my $count = $res3[0];
		if ($count gt 0) {
			next;
		}
	
		$cmd  = "select count(*) from `".$target_db."`.`LocStemEdAct".$chnstr."` ";
		$cmd .= "where begadr =  $begadr ";
		$cmd .= "and endadr   =  $endadr ";
		$cmd .= "and varid    = '$varid' ";
		$cmd .= "and varnew like '$varid%'; ";
		#print $cmd."\n";
		$sth2 = $dbh->prepare ($cmd);
		$sth2->execute ();
		@res2 = $sth2->fetchrow_array ();
		$count = $res2[0];
		#print $count."\n";
		if ($count eq 0) # set default values
		{
			# LocStemEd
			$cmd  = "update `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "set varnew = varid, ";
			$cmd .= "s1 = '*' ";
			$cmd .= "where varid = 'a' ";
			$cmd .= "and begadr =  $begadr ";
			$cmd .= "and endadr =  $endadr ";
			$cmd .= "and varid  = '$varid' ";
			$dbh->do ($cmd);
			$cmd  = "update `".$target_db."`.`LocStemEdAct".$chnstr."` ";
			$cmd .= "set s1 = 'a' ";
			$cmd .= "where varid not like 'a' ";
			$cmd .= "and begadr =  $begadr ";
			$cmd .= "and endadr =  $endadr ";
			$cmd .= "and varid  = '$varid' ";
			$dbh->do ($cmd);
			# VarGenAtt
			$cmd  = "update `".$target_db."`.`VarGenAttAct".$chnstr."` a, ";
			$cmd .= "`".$source_db."`.`VarGenAttAct".$chnstr."` b ";
			$cmd .= "set a.`varnew` = b.`varnew`, ";
			$cmd .= "a.`s1` = b.`s1` ";
			$cmd .= "where a.`begadr` = b.`begadr` ";
			$cmd .= "and a.`endadr` = b.`endadr` ";
			$cmd .= "and a.`varid` = b.`varid` ";
			$cmd .= "and a.`ms` = b.`ms`; ";
			$dbh->do ($cmd);
		}
	}
}
### Datenbankhandle freigeben und Programmende ###
$sth->finish ();
$sth3->finish ();
$sth4->finish ();
if ($sth2) 
{
	$sth2->finish ();
}
$dbh->disconnect ();
exit (0);
