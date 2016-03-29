#!/usr/bin/perl -w

##############################################################################################
#
#   file: isFehlvers.pm
#   author: volker.krueger@uni-muenster.de
#   date: 26. August 2014
#   
#   DEUTSCH:
#   Perlmodul stellt die Funktion 'isFehlvers(Anfangsadresse, Endadresse)' zur Verfügung.
#   Die Funktion 'decodeAdr' wird innerhalb von 'isFehlvers' aufgerufen.
#   Es wird die Datenbanktabelle `Apparat`.`Fehlverse` abgefragt und ausgewertet. Das Skript
#   greift jeweils auf den lokalen MySQL-Server zu.
#
#   Rückgabewerte:
#   Gehört die Adresse vollständig zu einem Fehlvers, so wird eine 0 zurückgegeben,
#   sonst eine 1.
#
#
#   ENGLISH:
#   The Nestle text contains some verses which probably not belong to the initial text.
#   This perl module contains the function 'isFehlvers'(begin_address, end_address).
#   The function 'decodeAdr' is called by 'isFehlvers'.
#   The script queries the database table `Apparat`.`Fehlverse`. The script is working
#   on the local MySQL server.
#
#   Return values:
#   If the address belongs totally to a Fehlvers the script will return 0, 
#   otherwise it will return 1.
#
##############################################################################################
use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:Apparat:localhost"; # data source name
my $user_name = getUsername();		 # user name
my $password = getPassword();		 # password

my $dbh = DBI->connect ($dsn, $user_name, $password,
			    	{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

sub decodeAdr
{
    my ($anfadr, $endadr, $len_anfadr);
    $anfadr = $_[0];
    $endadr = $_[1];
    my ($book, $chapter, $verse, $begin_word, $end_word, @result);
    $len_anfadr = length($anfadr);
    if ($len_anfadr == 8)
    {
        $book = substr($anfadr, 0, 1);
        $chapter = substr($anfadr, 1, 2);
        $verse = substr($anfadr, 3, 2);
        $begin_word = substr($anfadr, 5, 3);
        $end_word = substr($endadr, 5, 3);
        @result = (int($book), int($chapter), int($verse), int($begin_word), int($end_word));
        return @result;
    }
    else
    {
        if ($len_anfadr == 9)
        {
            $book = substr($anfadr, 0, 2);
            $chapter = substr($anfadr, 2, 2);
            $verse = substr($anfadr, 4, 2);
            $begin_word = substr($anfadr, 6, 3);
            $end_word = substr($endadr, 6, 3);
            @result = (int($book), int($chapter), int($verse), int($begin_word), int($end_word));
            return @result;
        }
    }
    return 1;
}
sub isFehlvers
{
    my ($anfadr, $endadr);
    $anfadr = $_[0];
    $endadr = $_[1];
    my ($sth, $sql, @ary);
    # decipher to book, chapter, verse and word
    my ($book, $chap, $verse, $begin_word, $end_word) = decodeAdr($anfadr, $endadr);
    # return true if passage belongs to a Fehlvers
    $sql = "select * from `Apparat`.`Fehlverse`;";
    $sth = $dbh->prepare($sql);
    $sth->execute();
    while (@ary = $sth->fetchrow_array())
    {
        my $bo = $ary[1];
        my $ch = $ary[2];
        my $sv = $ary[3];
		my $ev = $ary[4];
        my $aw = $ary[5];
        my $ew = $ary[6];
        if ($book == $bo && $chap == $ch && $verse >= $sv && $verse <= $ev && $begin_word >= $aw && $end_word <= $ew)
        {
            return 0;
        }
    }
    return 1;
}
1;
